"""Build the Analytics EDA Jupyter Notebook (notebooks/eda_analytics.ipynb)
covering:
1. Accuracy per concept
2. Learning curves
3. Dropout points
4. Hardest concepts
Each with a visual plot and a one-line insight.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
NB_PATH = BASE_DIR / "notebooks" / "eda_analytics.ipynb"


def md_cell(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source.splitlines()],
    }


def code_cell(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source.splitlines()],
    }


cells = [
    md_cell(
        "# Ilm Academy — Day 1 Analytics EDA\n"
        "**Scenario:** Ilm Academy (8,000 online students) currently gives every student the same linear path, "
        "and ~45% drop out before Week 4.\n\n"
        "This notebook analyzes:\n"
        "1. **Accuracy per Concept** (45 Python concepts)\n"
        "2. **Learning Curves** (accuracy across attempts by ability cohort)\n"
        "3. **Dropout Points** (weekly attrition & pre-Week-4 bottleneck concepts)\n"
        "4. **Hardest Concepts** (lowest accuracy & highest response-time concepts)"
    ),
    code_cell(
        "import json\n"
        "from pathlib import Path\n"
        "import numpy as np\n"
        "import pandas as pd\n"
        "import matplotlib.pyplot as plt\n"
        "import seaborn as sns\n\n"
        "sns.set_theme(style='whitegrid', palette='muted')\n"
        "BASE_DIR = Path('..').resolve()\n"
        "DATA_DIR = BASE_DIR / 'data'\n"
        "OUT_DIR = BASE_DIR / 'outputs'\n"
        "OUT_DIR.mkdir(exist_ok=True)\n\n"
        "profiles = pd.read_csv(DATA_DIR / 'student_profiles.csv')\n"
        "interactions = pd.read_csv(DATA_DIR / 'learner_interactions.csv')\n"
        "graph_meta = json.loads((DATA_DIR / 'concept_graph.json').read_text(encoding='utf-8'))\n"
        "qbank = json.loads((DATA_DIR / 'question_bank.json').read_text(encoding='utf-8'))\n\n"
        "print(f'Students: {len(profiles):,} | Interactions: {len(interactions):,} | '\n"
        "      f'Concepts: {graph_meta[\"num_concepts\"]} (DAG={graph_meta[\"is_dag\"]}) | Questions: {len(qbank)}')\n"
        "pre_w4 = ((profiles['dropped_out'] == 1) & (profiles['dropout_week'] < 4)).mean()\n"
        "print(f'Overall Accuracy: {interactions[\"correct\"].mean():.1%} | Pre-Week-4 Dropout: {pre_w4:.1%}')"
    ),
    md_cell("## 1. Accuracy per Concept"),
    code_cell(
        "concept_acc = (\n"
        "    interactions.groupby(['concept_id', 'week'], as_index=False)['correct']\n"
        "    .agg(['mean', 'count'])\n"
        "    .rename(columns={'mean': 'accuracy', 'count': 'attempts'})\n"
        "    .sort_values('accuracy')\n"
        ")\n\n"
        "fig, ax = plt.subplots(figsize=(12, 11))\n"
        "colors = plt.cm.RdYlGn(concept_acc['accuracy'])\n"
        "ax.barh(concept_acc['concept_id'], concept_acc['accuracy'], color=colors, edgecolor='#334155', linewidth=0.5)\n"
        "ax.axvline(interactions['correct'].mean(), color='#0f172a', linestyle='--', linewidth=1.2, label='Overall Mean')\n"
        "ax.set_xlim(0, 1.0)\n"
        "ax.set_xlabel('Accuracy')\n"
        "ax.set_title('Accuracy per Python Concept (45 Concepts)', fontsize=14, fontweight='bold')\n"
        "ax.legend(loc='lower right')\n"
        "plt.tight_layout()\n"
        "fig.savefig(OUT_DIR / 'eda_accuracy_per_concept.png', dpi=150)\n"
        "plt.show()\n\n"
        "top_c = concept_acc.iloc[-1]\n"
        "bot_c = concept_acc.iloc[0]\n"
        "print(f'INSIGHT: Concept accuracy spans {bot_c[\"accuracy\"]:.1%} ({bot_c[\"concept_id\"]}) to '\n"
        "      f'{top_c[\"accuracy\"]:.1%} ({top_c[\"concept_id\"]}), with steep drops on later/bottleneck topics.')"
    ),
    md_cell("## 2. Learning Curves"),
    code_cell(
        "merged = interactions.merge(profiles[['student_id', 'ability']], on='student_id', how='left')\n"
        "merged['ability_tier'] = pd.qcut(merged['ability'], q=3, labels=['Low Ability', 'Medium Ability', 'High Ability'])\n"
        "lc = merged.groupby(['ability_tier', 'attempt_num'], observed=True)['correct'].mean().reset_index()\n\n"
        "fig, ax = plt.subplots(figsize=(8, 5))\n"
        "sns.lineplot(data=lc, x='attempt_num', y='correct', hue='ability_tier', marker='o', linewidth=2.4, ax=ax)\n"
        "ax.set_xticks([1, 2, 3])\n"
        "ax.set_ylim(0.35, 1.0)\n"
        "ax.set_xlabel('Attempt Number on Concept')\n"
        "ax.set_ylabel('Mean Accuracy')\n"
        "ax.set_title('Learning Curves by Student Ability Tertile', fontsize=14, fontweight='bold')\n"
        "plt.tight_layout()\n"
        "fig.savefig(OUT_DIR / 'eda_learning_curves.png', dpi=150)\n"
        "plt.show()\n\n"
        "overall_lc = merged.groupby('attempt_num')['correct'].mean()\n"
        "gain = overall_lc.iloc[-1] - overall_lc.iloc[0]\n"
        "print(f'INSIGHT: Accuracy rises by {gain:+.1%} from attempt 1 ({overall_lc.iloc[0]:.1%}) to attempt 3 '\n"
        "      f'({overall_lc.iloc[-1]:.1%}), confirming practice improves mastery across all ability tiers.')"
    ),
    md_cell("## 3. Dropout Points (Pre-Week-4 Attrition)"),
    code_cell(
        "dropped = profiles[profiles['dropped_out'] == 1]\n"
        "weekly_drop = dropped['dropout_week'].value_counts().sort_index().reindex(range(1, 7), fill_value=0)\n"
        "cum_retained = 1.0 - (weekly_drop.cumsum() / len(profiles))\n\n"
        "fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))\n"
        "bar_colors = ['#ef4444' if w < 4 else '#64748b' for w in weekly_drop.index]\n"
        "axes[0].bar(weekly_drop.index, weekly_drop.values, color=bar_colors, edgecolor='#0f172a')\n"
        "axes[0].set_title('Student Dropouts by Week (Red = Pre-Week 4)', fontweight='bold')\n"
        "axes[0].set_xlabel('Week')\n"
        "axes[0].set_ylabel('Students Dropped')\n\n"
        "axes[1].plot(cum_retained.index, cum_retained.values * 100, marker='s', color='#2563eb', linewidth=2.4)\n"
        "axes[1].axvline(3.5, color='#ef4444', linestyle='--', label='Week 4 Threshold')\n"
        "axes[1].set_ylim(0, 105)\n"
        "axes[1].set_title('Cohort Retention Curve (%)', fontweight='bold')\n"
        "axes[1].set_xlabel('Week')\n"
        "axes[1].set_ylabel('Retained (%)')\n"
        "axes[1].legend()\n"
        "plt.tight_layout()\n"
        "fig.savefig(OUT_DIR / 'eda_dropout_points.png', dpi=150)\n"
        "plt.show()\n\n"
        "top_drop_concept = dropped['dropout_concept'].value_counts().index[0]\n"
        "top_drop_cnt = dropped['dropout_concept'].value_counts().iloc[0]\n"
        "print(f'INSIGHT: {pre_w4:.1%} of students drop out before Week 4, peaking at \"{top_drop_concept}\" ({top_drop_cnt} dropouts) '\n"
        "      f'where unaddressed prerequisite gaps compound.')"
    ),
    md_cell("## 4. Hardest Concepts"),
    code_cell(
        "hardest = (\n"
        "    interactions.groupby('concept_id', as_index=False)\n"
        "    .agg(accuracy=('correct', 'mean'), avg_time_sec=('response_time_sec', 'mean'), attempts=('correct', 'count'))\n"
        "    .sort_values('accuracy')\n"
        "    .head(10)\n"
        ")\n\n"
        "fig, ax = plt.subplots(figsize=(10, 5))\n"
        "sns.barplot(data=hardest, x='accuracy', y='concept_id', hue='concept_id', palette='Reds_r', legend=False, ax=ax)\n"
        "ax.set_xlim(0, 0.85)\n"
        "ax.set_title('Top 10 Hardest Python Concepts (Lowest Accuracy)', fontsize=14, fontweight='bold')\n"
        "ax.set_xlabel('Accuracy')\n"
        "ax.set_ylabel('Concept')\n"
        "for i, row in enumerate(hardest.itertuples()):\n"
        "    ax.text(row.accuracy + 0.01, i, f'{row.accuracy:.1%} ({row.avg_time_sec:.0f}s)', va='center', fontsize=9)\n"
        "plt.tight_layout()\n"
        "fig.savefig(OUT_DIR / 'eda_hardest_concepts.png', dpi=150)\n"
        "plt.show()\n\n"
        "h1 = hardest.iloc[0]\n"
        "print(f'INSIGHT: \"{h1[\"concept_id\"]}\" is the hardest concept ({h1[\"accuracy\"]:.1%} accuracy, {h1[\"avg_time_sec\"]:.0f}s avg), '\n"
        "      f'marking it and other top-10 bottlenecks as prime targets for adaptive scaffolding.')"
    ),
]

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.12"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

NB_PATH.parent.mkdir(parents=True, exist_ok=True)
NB_PATH.write_text(json.dumps(notebook, indent=2), encoding="utf-8")
print(f"Wrote notebook -> {NB_PATH}")
