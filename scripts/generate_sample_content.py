"""Generate realistic sample Ilm Academy Python lesson materials:
- PowerPoint slide decks (.pptx)
- PDF lecture notes (.pdf)
- Spoken-word lesson videos (.mp4) via Windows SAPI + ffmpeg
"""

import os
import subprocess
from pathlib import Path
import fitz  # PyMuPDF
from pptx import Presentation
from pptx.util import Inches, Pt

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
SLIDES_DIR = RAW_DIR / "slides"
NOTES_DIR = RAW_DIR / "notes"
VIDEOS_DIR = RAW_DIR / "videos"

LESSONS = [
    {
        "lesson_id": "L01",
        "week": 1,
        "title": "Python Variables, Data Types & Basic I/O",
        "concepts": ["variables", "data_types", "type_casting", "input_output", "string_formatting"],
        "slides": [
            ("Variables & Assignment", "A variable binds a name to an object in memory using =. Names use snake_case."),
            ("Core Data Types", "int (42), float (3.14), str ('Ilm'), bool (True/False), and NoneType."),
            ("Type Casting & Input", "input() always returns str. Use int(), float(), str() to convert types safely."),
            ("F-Strings", "Format output cleanly with f'Hello {name}, score: {score:.1f}'."),
        ],
        "notes": (
            "Lesson 1 Lecture Notes: Python Foundations.\n"
            "Variables in Python are dynamically typed references to objects. Use type(x) to inspect types.\n"
            "Common pitfall: concatenating str and int raises TypeError. Always cast with int() or str().\n"
            "F-strings (Python 3.6+) evaluate expressions inside curly braces and support format specifiers."
        ),
        "narration": (
            "Welcome to Ilm Academy Python Week One, Lesson One: Variables and Data Types. "
            "In Python, a variable is a name bound to an object in memory. "
            "The four core primitive types are integers, floating point numbers, strings, and booleans. "
            "Remember that the input function always returns a string, so you must cast it with int or float before doing math. "
            "Finally, use f strings for clean and readable string formatting."
        ),
    },
    {
        "lesson_id": "L02",
        "week": 1,
        "title": "Operators, Conditionals & Boolean Logic",
        "concepts": ["arithmetic_ops", "comparison_ops", "boolean_logic", "if_elif_else", "nested_conditionals"],
        "slides": [
            ("Arithmetic & Modulo", "Operators: +, -, *, / (float division), // (floor), % (modulo), ** (power)."),
            ("Comparison & Boolean Logic", "Comparisons (==, !=, <, >) return bool. Combine with and, or, not."),
            ("If / Elif / Else", "Branch execution based on truthy/falsy conditions. Indentation defines blocks."),
            ("Short-Circuit Evaluation", "Python stops evaluating 'and' on the first False, and 'or' on the first True."),
        ],
        "notes": (
            "Lesson 2 Lecture Notes: Control Flow.\n"
            "Use == for value equality and = for assignment. Modulo % is essential for divisibility checks.\n"
            "Truthy values: non-zero numbers, non-empty collections. Falsy: 0, '', [], {}, None, False.\n"
            "Avoid deep nesting by using elif chains or early returns."
        ),
        "narration": (
            "Welcome to Lesson Two: Operators and Conditionals. "
            "Python provides floor division with double slash and remainder with the modulo operator. "
            "Boolean logic uses the keywords and, or, and not, with short circuit evaluation. "
            "Use if, elif, and else statements with four space indentation to control program flow."
        ),
    },
    {
        "lesson_id": "L03",
        "week": 2,
        "title": "Loops, Iteration & Loop Control",
        "concepts": ["while_loops", "for_loops", "range_function", "break_continue", "nested_loops"],
        "slides": [
            ("While Loops", "Repeat a block while a condition remains True. Always update the loop variable!"),
            ("For Loops & range()", "Iterate over sequences with for item in seq. range(start, stop, step) excludes stop."),
            ("Break & Continue", "break exits the loop immediately; continue skips to the next iteration."),
            ("Nested Loops", "An inner loop runs completely for each iteration of the outer loop. O(n*m) complexity."),
        ],
        "notes": (
            "Lesson 3 Lecture Notes: Iteration.\n"
            "Infinite loops happen when the while condition never becomes False.\n"
            "Use enumerate(seq) when you need both index and value instead of range(len(seq)).\n"
            "Nested loops are used for 2D grids, multiplication tables, and pairwise comparisons."
        ),
        "narration": (
            "In Lesson Three we cover loops and iteration. "
            "A while loop repeats as long as a condition is true, so make sure your loop variable updates to avoid infinite loops. "
            "A for loop iterates over any sequence, and the range function generates integer sequences up to but excluding the stop value. "
            "Use break to exit early and continue to skip the current iteration."
        ),
    },
    {
        "lesson_id": "L04",
        "week": 2,
        "title": "Lists, Tuples, Indexing & Slicing",
        "concepts": ["lists", "list_indexing_slicing", "list_methods", "tuples", "mutability"],
        "slides": [
            ("Lists & Mutability", "Lists are ordered, mutable sequences: nums = [10, 20, 30]."),
            ("Indexing & Slicing", "Zero-based indexing; negative indices count from end. Slice syntax: seq[start:stop:step]."),
            ("List Methods", "append(), extend(), insert(), pop(), remove(), sort(), reverse()."),
            ("Tuples & Immutability", "Tuples (1, 2) are immutable ordered sequences, safe for fixed records and dict keys."),
        ],
        "notes": (
            "Lesson 4 Lecture Notes: Sequences.\n"
            "Slicing creates a shallow copy: nums[:] copies the list.\n"
            "Aliasing pitfall: b = a does NOT copy a list; both variables point to the same object.\n"
            "Tuples cannot be modified in-place, preventing accidental mutation."
        ),
        "narration": (
            "Lesson Four introduces lists and tuples. "
            "Lists are ordered and mutable, supporting indexing from zero and negative indexing from the end. "
            "Slicing with start, stop, and step extracts a subsequence as a new list. "
            "Tuples are immutable sequences, which makes them ideal for fixed records and dictionary keys."
        ),
    },
    {
        "lesson_id": "L05",
        "week": 3,
        "title": "Dictionaries, Sets & Hashing",
        "concepts": ["dictionaries", "dict_methods", "sets", "set_operations", "hashing_concepts"],
        "slides": [
            ("Dictionaries", "Key-value mappings with O(1) average lookup: student = {'name': 'Ali', 'score': 95}."),
            ("Safe Lookup & Iteration", "Use d.get(key, default) to avoid KeyError. Iterate with .keys(), .values(), .items()."),
            ("Sets", "Unordered collections of unique hashable elements: seen = set()."),
            ("Set Operations", "Union (|), intersection (&), difference (-), symmetric difference (^)."),
        ],
        "notes": (
            "Lesson 5 Lecture Notes: Hash-based Structures.\n"
            "Dictionary keys and set elements must be hashable (immutable types like int, str, tuple).\n"
            "Use sets for fast membership testing (x in my_set) in O(1) average time vs O(n) for lists."
        ),
        "narration": (
            "Welcome to Week Three, Lesson Five: Dictionaries and Sets. "
            "Dictionaries store key value pairs with constant time average lookup. "
            "Always use the get method when a key might be missing to avoid a KeyError. "
            "Sets store unique hashable items and support fast membership testing and mathematical set operations."
        ),
    },
    {
        "lesson_id": "L06",
        "week": 4,
        "title": "Functions, Scope & Recursion",
        "concepts": ["functions_def", "parameters_defaults", "return_values", "variable_scope", "lambda_functions", "recursion"],
        "slides": [
            ("Defining Functions", "def greet(name='Student'): encapsulates reusable logic."),
            ("Return vs Print", "return sends a value back to the caller; print only writes to stdout (returns None)."),
            ("LEGB Scope", "Local, Enclosing, Global, Built-in. Avoid mutating global state."),
            ("Recursion", "A function calling itself with a base case and a smaller recursive step."),
        ],
        "notes": (
            "Lesson 6 Lecture Notes: Functions & Recursion.\n"
            "Never use mutable default arguments like def f(items=[]):; use None instead.\n"
            "Every recursive function needs a base case to terminate and a recursive case that progresses toward it."
        ),
        "narration": (
            "In Week Four, Lesson Six, we study functions, scope, and recursion. "
            "Functions promote modularity. Remember the difference between return and print: a function without a return statement returns None. "
            "Python resolves names using the L E G B scope rule. "
            "Recursion solves a problem by breaking it into a base case and a smaller self similar subproblem."
        ),
    },
    {
        "lesson_id": "L07",
        "week": 5,
        "title": "Exceptions, File I/O & Comprehensions",
        "concepts": ["exceptions_try_except", "raising_exceptions", "file_io", "context_managers", "list_comprehensions", "generators"],
        "slides": [
            ("Try / Except / Finally", "Handle runtime errors gracefully without crashing the program."),
            ("Context Managers (with)", "with open('data.txt', 'r') as f: guarantees the file is closed automatically."),
            ("Comprehensions", "[x**2 for x in range(10) if x % 2 == 0] builds lists concisely."),
            ("Generators & yield", "Generators compute values lazily one at a time, saving memory on large streams."),
        ],
        "notes": (
            "Lesson 7 Lecture Notes: Robust Python & Pythonic Idioms.\n"
            "Catch specific exceptions (ValueError, FileNotFoundError) rather than bare except:.\n"
            "Generator expressions use parentheses (x*2 for x in data) and yield items on demand."
        ),
        "narration": (
            "Lesson Seven covers exception handling, file I O, and comprehensions. "
            "Use try and except blocks to catch specific errors like ValueError or FileNotFoundError. "
            "Always open files using a with context manager so resources are released safely. "
            "List comprehensions and generator expressions offer concise, Pythonic ways to transform data."
        ),
    },
    {
        "lesson_id": "L08",
        "week": 6,
        "title": "Object-Oriented Programming & Algorithmic Thinking",
        "concepts": ["classes_objects", "init_self", "inheritance", "encapsulation", "polymorphism", "time_complexity", "searching_sorting"],
        "slides": [
            ("Classes & __init__", "Classes bundle data (attributes) and behavior (methods). self refers to the instance."),
            ("Inheritance & Polymorphism", "Subclasses inherit and override parent methods using super()."),
            ("Encapsulation", "Hide internal state behind clean public methods; use _protected conventions."),
            ("Big-O & Search/Sort", "Linear search O(n) vs Binary search O(log n) on sorted data; Python sort is O(n log n)."),
        ],
        "notes": (
            "Lesson 8 Lecture Notes: OOP & Complexity.\n"
            "__init__ initializes a newly created instance; __repr__ provides a developer-friendly string.\n"
            "Binary search requires a sorted sequence and halves the search space each step."
        ),
        "narration": (
            "Welcome to our final Week Six lesson on Object Oriented Programming and Algorithmic Thinking. "
            "Classes define blueprints for objects, with dunder init setting initial attributes on self. "
            "Inheritance lets subclasses reuse and specialize parent behavior. "
            "Finally, analyzing Big O time complexity helps us choose binary search over linear search on sorted data."
        ),
    },
]


def build_slides(lesson: dict) -> Path:
    SLIDES_DIR.mkdir(parents=True, exist_ok=True)
    prs = Presentation()
    title_slide = prs.slides.add_slide(prs.slide_layouts[0])
    title_slide.shapes.title.text = f"{lesson['lesson_id']}: {lesson['title']}"
    title_slide.placeholders[1].text = f"Ilm Academy | Week {lesson['week']} | Concepts: {', '.join(lesson['concepts'])}"

    for heading, body in lesson["slides"]:
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = heading
        tf = slide.placeholders[1].text_frame
        tf.text = body
        for p in tf.paragraphs:
            p.font.size = Pt(20)

    out_path = SLIDES_DIR / f"{lesson['lesson_id']}.pptx"
    prs.save(out_path)
    return out_path


def build_pdf_notes(lesson: dict) -> Path:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    page = doc.new_page()
    text = f"{lesson['lesson_id']} - {lesson['title']} (Week {lesson['week']})\n\n{lesson['notes']}"
    page.insert_text((50, 60), text, fontsize=12)
    out_path = NOTES_DIR / f"{lesson['lesson_id']}.pdf"
    doc.save(out_path)
    doc.close()
    return out_path


def build_lesson_video(lesson: dict) -> Path:
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    wav_path = VIDEOS_DIR / f"{lesson['lesson_id']}.wav"
    mp4_path = VIDEOS_DIR / f"{lesson['lesson_id']}.mp4"

    # Synthesize real spoken narration via Windows System.Speech
    safe_text = lesson["narration"].replace("'", " ")
    ps_cmd = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.Rate = 1; "
        f"$s.SetOutputToWaveFile('{str(wav_path)}'); "
        f"$s.Speak('{safe_text}'); "
        "$s.Dispose()"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True)

    # Wrap WAV into an MP4 video with a dark-blue title card using ffmpeg
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=0x1e293b:s=640x360:r=1",
            "-i",
            str(wav_path),
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-c:a",
            "aac",
            "-b:a",
            "96k",
            "-shortest",
            str(mp4_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if wav_path.exists():
        wav_path.unlink()
    return mp4_path


def main():
    for lesson in LESSONS:
        pptx_p = build_slides(lesson)
        pdf_p = build_pdf_notes(lesson)
        mp4_p = build_lesson_video(lesson)
        print(f"Generated {lesson['lesson_id']}: {pptx_p.name}, {pdf_p.name}, {mp4_p.name}")


if __name__ == "__main__":
    main()
