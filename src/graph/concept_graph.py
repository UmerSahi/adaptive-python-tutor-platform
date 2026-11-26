"""Python Concept Graph (DAG) for Ilm Academy:
- 45 Python concepts with prerequisite edges
- Cycle detection (DAG verification)
- Lesson & Question Bank mapping
- JSON export + hierarchical visualization
"""

import json
from pathlib import Path
from typing import Any

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import networkx as nx

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"

# 45 Python concepts organized across Weeks 1-6
CONCEPTS: list[dict[str, Any]] = [
    # Week 1: Foundations & Control Flow (10 concepts)
    {"id": "variables", "name": "Variables & Assignment", "week": 1, "lesson_id": "L01", "tier": "Foundations", "prereqs": []},
    {"id": "data_types", "name": "Primitive Data Types", "week": 1, "lesson_id": "L01", "tier": "Foundations", "prereqs": ["variables"]},
    {"id": "type_casting", "name": "Type Casting", "week": 1, "lesson_id": "L01", "tier": "Foundations", "prereqs": ["data_types"]},
    {"id": "input_output", "name": "Console I/O", "week": 1, "lesson_id": "L01", "tier": "Foundations", "prereqs": ["variables", "type_casting"]},
    {"id": "string_formatting", "name": "String Formatting (f-strings)", "week": 1, "lesson_id": "L01", "tier": "Foundations", "prereqs": ["data_types", "input_output"]},
    {"id": "arithmetic_ops", "name": "Arithmetic & Modulo", "week": 1, "lesson_id": "L02", "tier": "Foundations", "prereqs": ["data_types"]},
    {"id": "comparison_ops", "name": "Comparison Operators", "week": 1, "lesson_id": "L02", "tier": "Control Flow", "prereqs": ["data_types", "arithmetic_ops"]},
    {"id": "boolean_logic", "name": "Boolean Logic (and/or/not)", "week": 1, "lesson_id": "L02", "tier": "Control Flow", "prereqs": ["comparison_ops"]},
    {"id": "if_elif_else", "name": "If / Elif / Else", "week": 1, "lesson_id": "L02", "tier": "Control Flow", "prereqs": ["boolean_logic"]},
    {"id": "nested_conditionals", "name": "Nested Conditionals", "week": 1, "lesson_id": "L02", "tier": "Control Flow", "prereqs": ["if_elif_else"]},

    # Week 2: Iteration & Sequences (10 concepts)
    {"id": "while_loops", "name": "While Loops", "week": 2, "lesson_id": "L03", "tier": "Iteration", "prereqs": ["boolean_logic", "if_elif_else"]},
    {"id": "range_function", "name": "range() Function", "week": 2, "lesson_id": "L03", "tier": "Iteration", "prereqs": ["arithmetic_ops"]},
    {"id": "for_loops", "name": "For Loops", "week": 2, "lesson_id": "L03", "tier": "Iteration", "prereqs": ["range_function", "if_elif_else"]},
    {"id": "break_continue", "name": "Break & Continue", "week": 2, "lesson_id": "L03", "tier": "Iteration", "prereqs": ["while_loops", "for_loops"]},
    {"id": "nested_loops", "name": "Nested Loops", "week": 2, "lesson_id": "L03", "tier": "Iteration", "prereqs": ["for_loops", "break_continue"]},
    {"id": "lists", "name": "Lists Creation & Basics", "week": 2, "lesson_id": "L04", "tier": "Data Structures", "prereqs": ["data_types", "for_loops"]},
    {"id": "list_indexing_slicing", "name": "Indexing & Slicing", "week": 2, "lesson_id": "L04", "tier": "Data Structures", "prereqs": ["lists"]},
    {"id": "list_methods", "name": "List Methods", "week": 2, "lesson_id": "L04", "tier": "Data Structures", "prereqs": ["lists"]},
    {"id": "mutability", "name": "Mutability & Aliasing", "week": 2, "lesson_id": "L04", "tier": "Data Structures", "prereqs": ["lists", "list_methods"]},
    {"id": "tuples", "name": "Tuples & Unpacking", "week": 2, "lesson_id": "L04", "tier": "Data Structures", "prereqs": ["list_indexing_slicing", "mutability"]},

    # Week 3: Strings, Dictionaries & Sets (7 concepts)
    {"id": "string_methods", "name": "String Methods", "week": 3, "lesson_id": "L05", "tier": "Data Structures", "prereqs": ["string_formatting", "list_indexing_slicing"]},
    {"id": "dictionaries", "name": "Dictionaries (Key-Value)", "week": 3, "lesson_id": "L05", "tier": "Data Structures", "prereqs": ["lists", "tuples"]},
    {"id": "dict_methods", "name": "Dictionary Methods & Iteration", "week": 3, "lesson_id": "L05", "tier": "Data Structures", "prereqs": ["dictionaries", "for_loops"]},
    {"id": "nested_structures", "name": "Nested Lists & Dicts", "week": 3, "lesson_id": "L05", "tier": "Data Structures", "prereqs": ["dict_methods", "nested_loops"]},
    {"id": "sets", "name": "Sets & Uniqueness", "week": 3, "lesson_id": "L05", "tier": "Data Structures", "prereqs": ["lists"]},
    {"id": "set_operations", "name": "Set Operations", "week": 3, "lesson_id": "L05", "tier": "Data Structures", "prereqs": ["sets"]},
    {"id": "hashing_concepts", "name": "Hashability & O(1) Lookup", "week": 3, "lesson_id": "L05", "tier": "Data Structures", "prereqs": ["dictionaries", "sets", "mutability"]},

    # Week 4: Functions & Recursion (7 concepts)
    {"id": "functions_def", "name": "Function Definition & Calls", "week": 4, "lesson_id": "L06", "tier": "Functions", "prereqs": ["if_elif_else", "for_loops"]},
    {"id": "parameters_defaults", "name": "Parameters & Default Args", "week": 4, "lesson_id": "L06", "tier": "Functions", "prereqs": ["functions_def", "mutability"]},
    {"id": "return_values", "name": "Return Values vs Print", "week": 4, "lesson_id": "L06", "tier": "Functions", "prereqs": ["functions_def"]},
    {"id": "variable_scope", "name": "Variable Scope (LEGB)", "week": 4, "lesson_id": "L06", "tier": "Functions", "prereqs": ["return_values"]},
    {"id": "args_kwargs", "name": "*args & **kwargs", "week": 4, "lesson_id": "L06", "tier": "Functions", "prereqs": ["parameters_defaults", "tuples", "dictionaries"]},
    {"id": "lambda_functions", "name": "Lambda & Higher-Order Funcs", "week": 4, "lesson_id": "L06", "tier": "Functions", "prereqs": ["return_values"]},
    {"id": "recursion", "name": "Recursion & Base Cases", "week": 4, "lesson_id": "L06", "tier": "Functions", "prereqs": ["return_values", "variable_scope"]},

    # Week 5: Exceptions, Files & Pythonic Idioms (6 concepts)
    {"id": "exceptions_try_except", "name": "Try / Except / Finally", "week": 5, "lesson_id": "L07", "tier": "Robust Python", "prereqs": ["if_elif_else", "functions_def"]},
    {"id": "raising_exceptions", "name": "Raising & Custom Exceptions", "week": 5, "lesson_id": "L07", "tier": "Robust Python", "prereqs": ["exceptions_try_except"]},
    {"id": "file_io", "name": "File Reading & Writing", "week": 5, "lesson_id": "L07", "tier": "Robust Python", "prereqs": ["string_methods", "exceptions_try_except"]},
    {"id": "context_managers", "name": "Context Managers (with)", "week": 5, "lesson_id": "L07", "tier": "Robust Python", "prereqs": ["file_io"]},
    {"id": "list_comprehensions", "name": "List & Dict Comprehensions", "week": 5, "lesson_id": "L07", "tier": "Robust Python", "prereqs": ["for_loops", "lists", "dict_methods"]},
    {"id": "generators", "name": "Generators & yield", "week": 5, "lesson_id": "L07", "tier": "Robust Python", "prereqs": ["list_comprehensions", "functions_def"]},

    # Week 6: OOP & Algorithmic Thinking (5 concepts) -> Total = 45 concepts
    {"id": "classes_objects", "name": "Classes & Objects", "week": 6, "lesson_id": "L08", "tier": "OOP & Algorithms", "prereqs": ["functions_def", "dictionaries"]},
    {"id": "init_self", "name": "__init__, self & Methods", "week": 6, "lesson_id": "L08", "tier": "OOP & Algorithms", "prereqs": ["classes_objects", "variable_scope"]},
    {"id": "inheritance", "name": "Inheritance & super()", "week": 6, "lesson_id": "L08", "tier": "OOP & Algorithms", "prereqs": ["init_self"]},
    {"id": "encapsulation", "name": "Encapsulation & Polymorphism", "week": 6, "lesson_id": "L08", "tier": "OOP & Algorithms", "prereqs": ["inheritance"]},
    {"id": "time_complexity", "name": "Big-O & Search/Sort", "week": 6, "lesson_id": "L08", "tier": "OOP & Algorithms", "prereqs": ["nested_loops", "recursion", "hashing_concepts"]},
]


def build_concept_graph(question_bank_path: Path | None = None) -> nx.DiGraph:
    """Construct the NetworkX DiGraph, verify DAG property, and attach lesson/question mappings."""
    G = nx.DiGraph()

    for c in CONCEPTS:
        G.add_node(
            c["id"],
            name=c["name"],
            week=c["week"],
            lesson_id=c["lesson_id"],
            tier=c["tier"],
            question_ids=[],
        )

    for c in CONCEPTS:
        for prereq in c["prereqs"]:
            if prereq not in G:
                raise ValueError(f"Unknown prerequisite '{prereq}' for concept '{c['id']}'")
            G.add_edge(prereq, c["id"])

    # Cycle check
    if not nx.is_directed_acyclic_graph(G):
        cycles = list(nx.simple_cycles(G))
        raise ValueError(f"Concept graph contains cycles: {cycles}")

    # Map questions if question bank exists
    if question_bank_path and question_bank_path.exists():
        questions = json.loads(question_bank_path.read_text(encoding="utf-8"))
        for q in questions:
            cid = q["concept_id"]
            if cid in G:
                G.nodes[cid]["question_ids"].append(q["id"])

    return G


def export_concept_graph(G: nx.DiGraph, out_path: Path = DATA_DIR / "concept_graph.json") -> Path:
    """Export the concept graph and topological order to JSON."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    topo_order = list(nx.topological_sort(G))
    payload = {
        "num_concepts": G.number_of_nodes(),
        "num_edges": G.number_of_edges(),
        "is_dag": nx.is_directed_acyclic_graph(G),
        "topological_order": topo_order,
        "nodes": [
            {"id": n, **G.nodes[n], "prerequisites": list(G.predecessors(n))}
            for n in topo_order
        ],
        "edges": [{"source": u, "target": v} for u, v in G.edges()],
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def visualize_concept_graph(
    G: nx.DiGraph, out_path: Path = OUTPUTS_DIR / "concept_graph.png"
) -> Path:
    """Render a clean hierarchical DAG visualization grouped by Week."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Assign (x, y) by week (x) and vertical index within week (y)
    by_week: dict[int, list[str]] = {}
    for n in nx.topological_sort(G):
        w = G.nodes[n]["week"]
        by_week.setdefault(w, []).append(n)

    pos: dict[str, tuple[float, float]] = {}
    for w, nodes in by_week.items():
        count = len(nodes)
        for i, n in enumerate(nodes):
            y = (count - 1) / 2.0 - i
            # Slight horizontal stagger to keep edges readable
            x = w * 2.4 + (0.25 if i % 2 else -0.25)
            pos[n] = (x, y * 1.15)

    week_colors = {
        1: "#3b82f6",  # Blue
        2: "#10b981",  # Emerald
        3: "#f59e0b",  # Amber
        4: "#8b5cf6",  # Violet
        5: "#ec4899",  # Pink
        6: "#ef4444",  # Red
    }
    node_colors = [week_colors[G.nodes[n]["week"]] for n in G.nodes()]

    fig, ax = plt.subplots(figsize=(20, 12), dpi=180)
    nx.draw_networkx_edges(
        G,
        pos,
        ax=ax,
        edge_color="#94a3b8",
        alpha=0.45,
        arrows=True,
        arrowsize=11,
        connectionstyle="arc3,rad=0.08",
        width=1.0,
    )
    nx.draw_networkx_nodes(
        G,
        pos,
        ax=ax,
        node_color=node_colors,
        node_size=950,
        edgecolors="#0f172a",
        linewidths=1.0,
    )
    labels = {n: G.nodes[n]["name"].replace(" ", "\n", 1) for n in G.nodes()}
    nx.draw_networkx_labels(
        G, pos, labels=labels, ax=ax, font_size=6.5, font_weight="bold", font_color="#0f172a"
    )

    legend_handles = [
        mpatches.Patch(color=col, label=f"Week {w}") for w, col in week_colors.items()
    ]
    ax.legend(handles=legend_handles, loc="upper left", frameon=True, fontsize=10)
    ax.set_title(
        f"Ilm Academy Python Concept Graph ({G.number_of_nodes()} Concepts, {G.number_of_edges()} Prerequisite Edges | DAG Verified)",
        fontsize=15,
        fontweight="bold",
        pad=16,
    )
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path


if __name__ == "__main__":
    qb_path = DATA_DIR / "question_bank.json"
    G = build_concept_graph(qb_path if qb_path.exists() else None)
    print(f"Concepts: {G.number_of_nodes()}, Edges: {G.number_of_edges()}, Is DAG: {nx.is_directed_acyclic_graph(G)}")
    json_p = export_concept_graph(G)
    img_p = visualize_concept_graph(G)
    print(f"Exported graph JSON -> {json_p}")
    print(f"Saved visualization -> {img_p}")
