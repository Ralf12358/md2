# Mermaid Auto-Layout Test

## Wide Diagram with Many Horizontal Elements

The diagram below has many horizontal elements and will automatically scale to full width:

### Dijkstra expandiert

```mermaid
flowchart TB
    D_Start[Start]
    D_L1_1[●]
    D_L1_2[●]
    D_L1_3[●]
    D_L1_4[●]
    D_L1_5[●]
    D_L1_6[●]
    D_L2_1[●]
    D_L2_2[●]
    D_L2_3[●]
    D_Ziel[Ziel]

    D_Start --- D_L1_1
    D_Start --- D_L1_2
    D_Start --- D_L1_3
    D_Start --- D_L1_4
    D_Start --- D_L1_5
    D_Start --- D_L1_6
    D_L1_1 --- D_L2_1
    D_L1_2 --- D_L2_1
    D_L1_3 --- D_L2_2
    D_L1_4 --- D_L2_2
    D_L1_5 --- D_L2_3
    D_L1_6 --- D_L2_3
    D_L2_1 --- D_Ziel
    D_L2_2 --- D_Ziel
    D_L2_3 --- D_Ziel

    D_text[Alle Richtungen]
    style D_text fill:#f9f,stroke:#333,stroke-width:2px
```

### A* expandiert

```mermaid
flowchart TB
    A_Start[Start]
    A_L1[●]
    A_L2_1[●]
    A_L2_2[●]
    A_L2_3[●]
    A_Ziel[Ziel]

    A_Start --- A_L1
    A_L1 --- A_L2_1
    A_L1 --- A_L2_2
    A_L1 --- A_L2_3
    A_L2_1 --- A_Ziel
    A_L2_2 --- A_Ziel
    A_L2_3 --- A_Ziel

    A_text[Fokussiert auf Ziel]
    style A_text fill:#9f9,stroke:#333,stroke-width:2px
```

## Narrow Diagram

This simpler diagram will automatically use less width:

```mermaid
flowchart TD
    A[Start] --> B[Process]
    B --> C[End]
```

## Manual Override

You can still override automatic sizing with width attribute:

```mermaid {width=50%}
flowchart LR
    X[Left] --> Y[Right]
```
