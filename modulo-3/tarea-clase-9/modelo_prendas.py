"""Entrena una CNN para clasificar prendas del Clothing Dataset de Kaggle.

Dataset: https://www.kaggle.com/datasets/agrigorev/clothing-dataset-full

Ejemplos:
    python modelo_prendas.py --epochs 15
    python modelo_prendas.py --predict data/images_compressed/3b86d877-2b9e-4c8b-a6a2-1d87513309d0.jpg
"""

import argparse
import json
import random
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from tensorflow import keras
from tensorflow.keras import layers

matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = BASE_DIR / "data"
DEFAULT_OUTPUT_DIR = BASE_DIR / "artifacts"
DEFAULT_CLASSES = [
    "T-Shirt",
    "Longsleeve",
    "Pants",
    "Shoes",
    "Shirt",
    "Dress",
    "Outwear",
    "Shorts",
    "Hat",
    "Skirt",
]
IMAGE_SIZE = 160
SEED = 42


def parse_args():
    parser = argparse.ArgumentParser(
        description="Entrena o utiliza una red neuronal para clasificar prendas."
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--epochs",
        type=int,
        default=12,
        help="Epocas con la base MobileNetV2 congelada.",
    )
    parser.add_argument(
        "--fine-tune-epochs",
        type=int,
        default=8,
        help="Epocas adicionales ajustando las ultimas capas de MobileNetV2.",
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument(
        "--classes",
        nargs="+",
        default=DEFAULT_CLASSES,
        help="Etiquetas del CSV que se utilizaran (minimo dos).",
    )
    parser.add_argument(
        "--predict",
        type=Path,
        metavar="IMAGE",
        help="Clasifica una imagen con un modelo ya entrenado.",
    )
    return parser.parse_args()


def set_reproducibility():
    random.seed(SEED)
    np.random.seed(SEED)
    tf.random.set_seed(SEED)


def load_records(data_dir, selected_classes):
    csv_path = data_dir / "images.csv"
    images_dir = data_dir / "images_compressed"
    if not csv_path.is_file() or not images_dir.is_dir():
        raise FileNotFoundError(
            f"Se esperaban {csv_path} y el directorio {images_dir}."
        )
    if len(selected_classes) < 2:
        raise ValueError("Se necesitan al menos dos clases para entrenar el modelo.")

    records = pd.read_csv(csv_path)
    available = set(records["label"].unique())
    unknown = set(selected_classes) - available
    if unknown:
        raise ValueError(f"Clases inexistentes en images.csv: {sorted(unknown)}")

    records = records[records["label"].isin(selected_classes)].copy()
    class_names = [name for name in selected_classes if name in set(records["label"])]
    class_to_id = {name: index for index, name in enumerate(class_names)}
    records["class_id"] = records["label"].map(class_to_id)
    records["path"] = records["image"].map(
        lambda image_id: str(images_dir / f"{image_id}.jpg")
    )
    records = records[records["path"].map(lambda path: Path(path).is_file())]

    counts = records["label"].value_counts().reindex(class_names)
    if (counts < 10).any():
        too_small = counts[counts < 10].to_dict()
        raise ValueError(f"Cada clase necesita al menos 10 imagenes: {too_small}")

    print("\nImagenes por clase:")
    print(counts.to_string())
    return records, class_names


def split_records(records):
    train, remaining = train_test_split(
        records,
        test_size=0.30,
        random_state=SEED,
        stratify=records["class_id"],
    )
    validation, test = train_test_split(
        remaining,
        test_size=0.50,
        random_state=SEED,
        stratify=remaining["class_id"],
    )
    print(
        f"\nDivision: {len(train)} entrenamiento, {len(validation)} validacion, "
        f"{len(test)} prueba."
    )
    return train, validation, test


def decode_image(path, label):
    image = tf.io.read_file(path)
    image = tf.io.decode_jpeg(image, channels=3)
    image = tf.image.resize_with_pad(image, IMAGE_SIZE, IMAGE_SIZE)
    image.set_shape((IMAGE_SIZE, IMAGE_SIZE, 3))
    return image, label


def make_dataset(records, batch_size, training=False):
    dataset = tf.data.Dataset.from_tensor_slices(
        (records["path"].to_numpy(), records["class_id"].to_numpy())
    )
    if training:
        dataset = dataset.shuffle(len(records), seed=SEED, reshuffle_each_iteration=True)
    return (
        dataset.map(decode_image, num_parallel_calls=tf.data.AUTOTUNE)
        .batch(batch_size)
        .prefetch(tf.data.AUTOTUNE)
    )


def build_model(number_of_classes):
    augmentation = keras.Sequential(
        [
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.05),
            layers.RandomZoom(0.10),
        ],
        name="aumento_datos",
    )
    base_model = keras.applications.MobileNetV2(
        input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False

    inputs = keras.Input((IMAGE_SIZE, IMAGE_SIZE, 3))
    x = augmentation(inputs)
    x = layers.Rescaling(1.0 / 127.5, offset=-1)(x)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.30)(x)
    outputs = layers.Dense(number_of_classes, activation="softmax")(x)
    model = keras.Model(inputs, outputs, name="clasificador_prendas_mobilenetv2")
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss=keras.losses.SparseCategoricalCrossentropy(),
        metrics=["accuracy"],
    )
    return model, base_model


def make_callbacks(model_path, initial_best=None):
    return [
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=3, restore_best_weights=True
        ),
        keras.callbacks.ModelCheckpoint(
            model_path,
            monitor="val_loss",
            save_best_only=True,
            initial_value_threshold=initial_best,
        ),
    ]


def save_training_history(frozen_history, fine_tune_history, output_dir):
    frames = []
    next_epoch = 1
    for phase, history in (
        ("base_congelada", frozen_history),
        ("ajuste_fino", fine_tune_history),
    ):
        if history is None:
            continue
        frame = pd.DataFrame(history.history)
        frame.insert(0, "epoch", range(next_epoch, next_epoch + len(frame)))
        frame.insert(1, "phase", phase)
        frames.append(frame)
        next_epoch += len(frame)

    history = pd.concat(frames, ignore_index=True)
    history.to_csv(output_dir / "historial.csv", index=False)
    figure, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].plot(history["epoch"], history["loss"], label="entrenamiento")
    axes[0].plot(history["epoch"], history["val_loss"], label="validacion")
    axes[0].set(title="Perdida", xlabel="Epoca")
    axes[1].plot(history["epoch"], history["accuracy"], label="entrenamiento")
    axes[1].plot(history["epoch"], history["val_accuracy"], label="validacion")
    axes[1].set(title="Exactitud", xlabel="Epoca")
    for axis in axes:
        axis.grid(alpha=0.25)
        axis.legend()
    figure.tight_layout()
    figure.savefig(output_dir / "curvas_entrenamiento.png", dpi=150)
    plt.close(figure)


def train(args):
    records, class_names = load_records(args.data_dir, args.classes)
    train_records, validation_records, test_records = split_records(records)
    train_data = make_dataset(train_records, args.batch_size, training=True)
    validation_data = make_dataset(validation_records, args.batch_size)
    test_data = make_dataset(test_records, args.batch_size)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    model_path = args.output_dir / "modelo_prendas.keras"
    labels_path = args.output_dir / "clases.json"
    labels_path.write_text(json.dumps(class_names, indent=2), encoding="utf-8")

    model, base_model = build_model(len(class_names))
    model.summary()
    weights = compute_class_weight(
        class_weight="balanced",
        classes=np.arange(len(class_names)),
        y=train_records["class_id"],
    )
    class_weights = dict(enumerate(weights))
    print("\nFase 1: entrenamiento del clasificador con MobileNetV2 congelada.")
    frozen_history = model.fit(
        train_data,
        validation_data=validation_data,
        epochs=args.epochs,
        class_weight=class_weights,
        callbacks=make_callbacks(model_path),
        shuffle=False,
    )

    frozen_validation_loss = model.evaluate(validation_data, verbose=0)[0]
    fine_tune_history = None
    if args.fine_tune_epochs > 0:
        print("\nFase 2: ajuste fino de las ultimas 30 capas de MobileNetV2.")
        base_model.trainable = True
        for layer in base_model.layers[:-30]:
            layer.trainable = False
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=1e-5),
            loss=keras.losses.SparseCategoricalCrossentropy(),
            metrics=["accuracy"],
        )
        fine_tune_history = model.fit(
            train_data,
            validation_data=validation_data,
            epochs=args.fine_tune_epochs,
            class_weight=class_weights,
            callbacks=make_callbacks(model_path, frozen_validation_loss),
            shuffle=False,
        )

    save_training_history(frozen_history, fine_tune_history, args.output_dir)
    model = keras.models.load_model(model_path)

    loss, accuracy = model.evaluate(test_data, verbose=0)
    probabilities = model.predict(test_data, verbose=0)
    predicted = probabilities.argmax(axis=1)
    expected = test_records["class_id"].to_numpy()
    print(f"\nPerdida de prueba: {loss:.4f}")
    print(f"Exactitud de prueba: {accuracy:.2%}\n")
    print(classification_report(expected, predicted, target_names=class_names, digits=3))
    print("Matriz de confusion (filas=reales, columnas=predicciones):")
    print(confusion_matrix(expected, predicted))
    print(f"\nModelo guardado en: {model_path}")
    print(f"Clases guardadas en: {labels_path}")
    print(f"Curvas guardadas en: {args.output_dir / 'curvas_entrenamiento.png'}")


def predict(args):
    model_path = args.output_dir / "modelo_prendas.keras"
    labels_path = args.output_dir / "clases.json"
    if not args.predict.is_file():
        raise FileNotFoundError(f"No existe la imagen: {args.predict}")
    if not model_path.is_file() or not labels_path.is_file():
        raise FileNotFoundError("Primero entrena el modelo para generar artifacts/.")

    model = keras.models.load_model(model_path)
    class_names = json.loads(labels_path.read_text(encoding="utf-8"))
    image, _ = decode_image(str(args.predict), 0)
    probabilities = model.predict(tf.expand_dims(image, axis=0), verbose=0)[0]
    top = np.argsort(probabilities)[::-1][: min(3, len(class_names))]
    print(f"\nPrediccion para {args.predict}:")
    for index in top:
        print(f"  {class_names[index]}: {probabilities[index]:.2%}")


def main():
    args = parse_args()
    if args.epochs < 1:
        raise ValueError("--epochs debe ser mayor o igual que 1.")
    if args.fine_tune_epochs < 0:
        raise ValueError("--fine-tune-epochs no puede ser negativo.")
    if args.batch_size < 1:
        raise ValueError("--batch-size debe ser mayor o igual que 1.")
    set_reproducibility()
    if args.predict:
        predict(args)
    else:
        train(args)


if __name__ == "__main__":
    main()
