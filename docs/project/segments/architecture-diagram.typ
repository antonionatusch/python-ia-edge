#import "@preview/mmdr:0.2.2": mermaid
#import "../utils/figures.typ": apa-figure

#let architecture_diagram = [
  #apa-figure(
    mermaid(
      "
      graph TB
          subgraph Tailscale[\"Red Tailscale (100.x.x.x/24)\"]
              direction LR
              Phone[\"Teléfono Físico<br/>Flutter App\"]
              Emulator[\"Emulador Android Studio<br/>Flutter App\"]
          end
          Laptop[\"Laptop Personal<br/>(WSL2 / Linux)\"]
          subgraph Supabase[\"Supabase Local (WSL)\"]
              direction TB
              API[\"Supabase API<br/>Puerto 42691\"]
              PG[(\"PostgreSQL 17<br/>Puerto 42692\")]
              Auth[\"Supabase Auth<br/>OTP / Email\"]
              Storage[(\"Supabase Storage<br/>dish-photos\")]
              RPCs[\"PL/pgSQL RPCs\"]
              API --> PG
              API --> Auth
              API --> Storage
              PG --> RPCs
              Storage --> RPCs
          end
          subgraph Flutter[\"App Flutter (MVVM + Provider)\"]
              direction TB
              Views[\"Views / Screens\"]
              ViewModels[\"ViewModels (ChangeNotifier)\"]
              Repos[\"Repositories\"]
              Services[\"Services\"]
              TFLite[\"TensorFlow Lite<br/>food_classifier.tflite\"]
              OSM[\"OpenStreetMap<br/>flutter_map\"]
              Views --> ViewModels
              ViewModels --> Repos
              ViewModels --> Services
              Services --> TFLite
              Services --> OSM
          end
          Laptop -->|\"hosts\"| API
          Phone -->|\"HTTP\"| API
          Emulator -->|\"HTTP\"| API
          Repos -.->|\"Supabase SDK\"| API
      ",
      base-theme: "default",
      theme: (
        background: "#FFF9F2",
        primary_color: "#FFFFFF",
        primary_text_color: "#000000",
        primary_border_color: "#C95714",
        secondary_color: "#FFFDF9",
        secondary_text_color: "#000000",
        secondary_border_color: "#ED6E1F",
        tertiary_color: "#F7E8DA",
        line_color: "#D9B89B",
        line_width: 27,
      ),
      layout: (
        node_spacing: 50,
      ),
    ),
    caption: "Diagrama de arquitectura del sistema de monitoreo",
    note: [Elaborado utilizando mmdr @MmdrTypst,
      un plugin de Typst @TypstApp
      para renderizar diagramas de Mermaid.js. @MermaidJs],
  )
]
