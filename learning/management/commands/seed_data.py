from django.core.management.base import BaseCommand
from django.utils.text import slugify
from learning.models import Topic, Chapter, Lesson


SEED_DATA = [
    {
        'title': 'Python',
        'order': 1,
        'icon_html': '<i class="fa-brands fa-python"></i>',
        'featured': True,
        'description': 'Master Python from fundamentals to advanced topics. Python is the most versatile and beginner-friendly language, powering web apps, data science, automation, and AI.',
        'chapters': [
            {
                'title': 'Python Basics',
                'description': 'Learn the core building blocks of Python — variables, data types, operators, and basic I/O.',
                'order': 1,
                'lessons': [
                    {
                        'title': 'Variables & Data Types',
                        'order': 1,
                        'difficulty': 'beginner',
                        'featured': True,
                        'summary': 'Understand how Python stores and categorizes data using variables and built-in types.',
                        'reading_time': 6,
                        'content': (
                            '<h2>What Are Variables?</h2>'
                            '<p>A variable is a named container that stores a value. In Python, you create a variable simply by assigning a value to a name.</p>'
                            '<p>Python is <strong>dynamically typed</strong> — you don\'t need to declare the type; Python infers it automatically.</p>'
                            '<h2>Built-in Data Types</h2>'
                            '<p>Python has several built-in data types:</p>'
                            '<ul>'
                            '<li><code>int</code> — whole numbers: <code>42</code></li>'
                            '<li><code>float</code> — decimal numbers: <code>3.14</code></li>'
                            '<li><code>str</code> — text: <code>"hello"</code></li>'
                            '<li><code>bool</code> — <code>True</code> or <code>False</code></li>'
                            '<li><code>list</code> — ordered, mutable sequence: <code>[1, 2, 3]</code></li>'
                            '<li><code>dict</code> — key-value store: <code>{"name": "Alice"}</code></li>'
                            '</ul>'
                            '<h2>Checking Types</h2>'
                            '<pre class="language-python"><code># Create variables\nage = 25\nprice = 19.99\nname = "Alice"\n\nprint(type(age))    # &lt;class \'int\'&gt;\nprint(type(price))  # &lt;class \'float\'&gt;\nprint(type(name))   # &lt;class \'str\'&gt;</code></pre>'
                            '<h2>Multiple Assignment</h2>'
                            '<pre class="language-python"><code>a, b, c = 10, 20, 30\nprint(a, b, c)  # 10 20 30\n\n# Swap without temp variable\na, b = b, a</code></pre>'
                        ),
                    },
                    {
                        'title': 'Control Flow',
                        'order': 2,
                        'difficulty': 'beginner',
                        'featured': True,
                        'summary': 'Direct the flow of your programs with if/elif/else statements and loops.',
                        'reading_time': 7,
                        'content': (
                            '<h2>Conditional Statements</h2>'
                            '<p>Python uses <code>if</code>, <code>elif</code>, and <code>else</code> to execute code based on conditions. Indentation defines blocks — no curly braces needed.</p>'
                            '<pre class="language-python"><code>score = 75\n\nif score &gt;= 90:\n    grade = "A"\nelif score &gt;= 80:\n    grade = "B"\nelif score &gt;= 70:\n    grade = "C"\nelse:\n    grade = "F"\n\nprint(f"Grade: {grade}")  # Grade: C</code></pre>'
                            '<h2>For Loops</h2>'
                            '<pre class="language-python"><code>fruits = ["apple", "banana", "cherry"]\nfor fruit in fruits:\n    print(fruit)\n\nfor i in range(5):\n    print(i)  # 0 1 2 3 4</code></pre>'
                            '<h2>While Loops</h2>'
                            '<pre class="language-python"><code>count = 0\nwhile count &lt; 5:\n    print(count)\n    count += 1</code></pre>'
                        ),
                    },
                ],
            },
            {
                'title': 'Functions & Modules',
                'description': 'Write reusable code with functions, understand scope, and organise code into modules.',
                'order': 2,
                'lessons': [
                    {
                        'title': 'Defining Functions',
                        'order': 1,
                        'difficulty': 'beginner',
                        'featured': False,
                        'summary': 'Learn how to define and call functions, use parameters and return values.',
                        'reading_time': 8,
                        'content': (
                            '<h2>Defining a Function</h2>'
                            '<p>Use the <code>def</code> keyword to define a function. Functions group reusable logic under a meaningful name.</p>'
                            '<pre class="language-python"><code>def greet(name):\n    return f"Hello, {name}!"\n\nprint(greet("Alice"))  # Hello, Alice!</code></pre>'
                            '<h2>Default Parameters</h2>'
                            '<pre class="language-python"><code>def greet(name, greeting="Hello"):\n    return f"{greeting}, {name}!"\n\nprint(greet("Bob"))        # Hello, Bob!\nprint(greet("Bob", "Hi")) # Hi, Bob!</code></pre>'
                            '<h2>*args and **kwargs</h2>'
                            '<pre class="language-python"><code>def add(*numbers):\n    return sum(numbers)\n\nprint(add(1, 2, 3, 4))  # 10</code></pre>'
                        ),
                    },
                ],
            },
        ],
    },
    {
        'title': 'JavaScript',
        'order': 2,
        'icon_html': '<i class="fa-brands fa-js"></i>',
        'featured': True,
        'description': 'JavaScript is the language of the web. Learn the fundamentals, modern ES6+ features, async programming, and how to build interactive applications.',
        'chapters': [
            {
                'title': 'JS Fundamentals',
                'description': 'Get up to speed with variables, types, operators, and basic control flow in JavaScript.',
                'order': 1,
                'lessons': [
                    {
                        'title': 'let, const & var',
                        'order': 1,
                        'difficulty': 'beginner',
                        'featured': True,
                        'summary': 'Understand the three ways to declare variables in JavaScript and when to use each.',
                        'reading_time': 5,
                        'content': (
                            '<h2>Variable Declarations</h2>'
                            '<p>JavaScript has three keywords for declaring variables. Modern JS uses <code>let</code> and <code>const</code> exclusively.</p>'
                            '<pre class="language-javascript"><code>const PI = 3.14;\n\nlet count = 0;\ncount += 1;\n\n// Avoid var in modern code\nvar legacy = "old style";</code></pre>'
                            '<h2>When to Use Which</h2>'
                            '<ul>'
                            '<li>Use <code>const</code> by default.</li>'
                            '<li>Use <code>let</code> when you need to reassign.</li>'
                            '<li>Never use <code>var</code> in new code.</li>'
                            '</ul>'
                        ),
                    },
                    {
                        'title': 'Functions & Arrow Functions',
                        'order': 2,
                        'difficulty': 'beginner',
                        'featured': False,
                        'summary': 'Master function declarations, expressions, and modern arrow function syntax.',
                        'reading_time': 7,
                        'content': (
                            '<h2>Function Declaration</h2>'
                            '<pre class="language-javascript"><code>function add(a, b) {\n  return a + b;\n}\nconsole.log(add(2, 3));  // 5</code></pre>'
                            '<h2>Arrow Functions</h2>'
                            '<pre class="language-javascript"><code>const add = (a, b) => a + b;\nconst double = x => x * 2;\n\nconsole.log(double(5));  // 10</code></pre>'
                        ),
                    },
                ],
            },
        ],
    },
    {
        'title': 'HTML & CSS',
        'order': 3,
        'icon_html': '<i class="fa-brands fa-html5"></i>',
        'featured': True,
        'description': 'Build the structure and style of web pages. Master semantic HTML5, modern CSS layouts (Flexbox & Grid), responsive design, and CSS custom properties.',
        'chapters': [
            {
                'title': 'HTML Fundamentals',
                'description': 'Learn the building blocks of every web page — elements, attributes, and semantic markup.',
                'order': 1,
                'lessons': [
                    {
                        'title': 'Document Structure',
                        'order': 1,
                        'difficulty': 'beginner',
                        'featured': True,
                        'summary': 'Understand the anatomy of an HTML document and how browsers parse it.',
                        'reading_time': 5,
                        'content': (
                            '<h2>Anatomy of an HTML Page</h2>'
                            '<pre class="language-html"><code>&lt;!DOCTYPE html&gt;\n&lt;html lang="en"&gt;\n&lt;head&gt;\n  &lt;meta charset="UTF-8" /&gt;\n  &lt;title&gt;My Page&lt;/title&gt;\n&lt;/head&gt;\n&lt;body&gt;\n  &lt;h1&gt;Hello, World!&lt;/h1&gt;\n&lt;/body&gt;\n&lt;/html&gt;</code></pre>'
                            '<h2>Semantic Elements</h2>'
                            '<ul>'
                            '<li><code>&lt;header&gt;</code> — page or section header</li>'
                            '<li><code>&lt;nav&gt;</code> — navigation links</li>'
                            '<li><code>&lt;main&gt;</code> — primary content</li>'
                            '<li><code>&lt;article&gt;</code> — self-contained content</li>'
                            '<li><code>&lt;footer&gt;</code> — page or section footer</li>'
                            '</ul>'
                        ),
                    },
                ],
            },
            {
                'title': 'CSS Layouts',
                'description': 'Master Flexbox and Grid to build modern, responsive layouts with ease.',
                'order': 2,
                'lessons': [
                    {
                        'title': 'Flexbox',
                        'order': 1,
                        'difficulty': 'intermediate',
                        'featured': False,
                        'summary': 'Use Flexbox to create one-dimensional layouts and align items with ease.',
                        'reading_time': 8,
                        'content': (
                            '<h2>Flexbox Basics</h2>'
                            '<pre class="language-css"><code>.container {\n  display: flex;\n  justify-content: space-between;\n  align-items: center;\n  gap: 1rem;\n}</code></pre>'
                            '<h2>Center Anything</h2>'
                            '<pre class="language-css"><code>.center {\n  display: flex;\n  justify-content: center;\n  align-items: center;\n}</code></pre>'
                        ),
                    },
                ],
            },
        ],
    },
    {
        'title': 'React',
        'order': 4,
        'icon_html': '<i class="fa-brands fa-react"></i>',
        'featured': False,
        'description': 'Build modern, component-based UIs with React. Learn JSX, hooks, state management, and how to connect your frontend to APIs.',
        'chapters': [
            {
                'title': 'React Basics',
                'description': 'Learn components, JSX, props, and state — the four pillars of every React app.',
                'order': 1,
                'lessons': [
                    {
                        'title': 'Components & JSX',
                        'order': 1,
                        'difficulty': 'intermediate',
                        'featured': False,
                        'summary': 'Understand how React components and JSX work together to build UIs declaratively.',
                        'reading_time': 7,
                        'content': (
                            '<h2>Your First Component</h2>'
                            '<pre class="language-jsx"><code>function Greeting({ name }) {\n  return (\n    &lt;div className="greeting"&gt;\n      &lt;h1&gt;Hello, {name}!&lt;/h1&gt;\n    &lt;/div&gt;\n  );\n}\n\nexport default Greeting;</code></pre>'
                            '<h2>Key JSX Rules</h2>'
                            '<ul>'
                            '<li>Use <code>className</code> instead of <code>class</code></li>'
                            '<li>Every component returns a single root element</li>'
                            '<li>JavaScript expressions go inside <code>{}</code></li>'
                            '</ul>'
                        ),
                    },
                    {
                        'title': 'useState & useEffect',
                        'order': 2,
                        'difficulty': 'intermediate',
                        'featured': True,
                        'summary': 'Manage local state and side-effects in functional components using React hooks.',
                        'reading_time': 9,
                        'content': (
                            '<h2>useState</h2>'
                            '<pre class="language-jsx"><code>import { useState } from "react";\n\nfunction Counter() {\n  const [count, setCount] = useState(0);\n  return (\n    &lt;button onClick={() =&gt; setCount(c =&gt; c + 1)}&gt;\n      Clicked {count} times\n    &lt;/button&gt;\n  );\n}</code></pre>'
                            '<h2>useEffect</h2>'
                            '<pre class="language-jsx"><code>useEffect(() =&gt; {\n  fetch("/api/users")\n    .then(r =&gt; r.json())\n    .then(setUsers);\n}, []); // runs once on mount</code></pre>'
                        ),
                    },
                ],
            },
        ],
    },
    {
        'title': 'SQL & Databases',
        'order': 5,
        'icon_html': '<i class="fa-solid fa-database"></i>',
        'featured': False,
        'description': 'Learn to design, query, and manage relational databases using SQL. Covers SELECT basics to joins, indexes, and transactions.',
        'chapters': [
            {
                'title': 'SQL Fundamentals',
                'description': 'Learn the core SQL commands: SELECT, INSERT, UPDATE, DELETE, and how to filter and sort data.',
                'order': 1,
                'lessons': [
                    {
                        'title': 'SELECT & Filtering',
                        'order': 1,
                        'difficulty': 'beginner',
                        'featured': False,
                        'summary': 'Query data from tables using SELECT, WHERE, ORDER BY, and LIMIT.',
                        'reading_time': 6,
                        'content': (
                            '<h2>Basic SELECT</h2>'
                            '<pre class="language-sql"><code>SELECT * FROM users;\nSELECT id, name, email FROM users;\nSELECT * FROM users WHERE age &gt; 18;\nSELECT * FROM users ORDER BY name ASC;\nSELECT * FROM users LIMIT 10;</code></pre>'
                        ),
                    },
                ],
            },
        ],
    },
    {
        'title': 'Git & Version Control',
        'order': 6,
        'icon_html': '<i class="fa-brands fa-git-alt"></i>',
        'featured': False,
        'description': 'Master Git — the most widely used version control system. Learn branching, merging, rebasing, and best practices for collaboration.',
        'chapters': [
            {
                'title': 'Git Basics',
                'description': 'Set up Git, understand the staging area, make commits, and manage your repository history.',
                'order': 1,
                'lessons': [
                    {
                        'title': 'Your First Repository',
                        'order': 1,
                        'difficulty': 'beginner',
                        'featured': False,
                        'summary': 'Initialise a repo, stage files, commit changes, and understand the three-tree architecture.',
                        'reading_time': 6,
                        'content': (
                            '<h2>Core Workflow</h2>'
                            '<pre class="language-bash"><code>git init\ngit status\ngit add .\ngit commit -m "Initial commit"\ngit log --oneline</code></pre>'
                            '<h2>Branching</h2>'
                            '<pre class="language-bash"><code>git checkout -b feature/login\ngit switch main\ngit merge feature/login</code></pre>'
                        ),
                    },
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed the database with initial learning content (safe to run multiple times)'

    def handle(self, *args, **options):
        created_topics = 0
        created_chapters = 0
        created_lessons = 0

        for topic_data in SEED_DATA:
            chapters_data = topic_data.pop('chapters', [])
            topic, t_created = Topic.objects.update_or_create(
                slug=slugify(topic_data['title']),
                defaults={
                    'title': topic_data['title'],
                    'description': topic_data['description'],
                    'icon_html': topic_data.get('icon_html', '<i class="fa-solid fa-book"></i>'),
                    'featured': topic_data.get('featured', False),
                    'order': topic_data.get('order', 0),
                    'is_published': True,
                },
            )
            if t_created:
                created_topics += 1

            for chapter_data in chapters_data:
                lessons_data = chapter_data.pop('lessons', [])
                chapter, c_created = Chapter.objects.update_or_create(
                    slug=slugify(f"{topic_data['title']}-{chapter_data['title']}"),
                    defaults={
                        'topic': topic,
                        'title': chapter_data['title'],
                        'description': chapter_data['description'],
                        'order': chapter_data.get('order', 0),
                        'is_published': True,
                    },
                )
                if c_created:
                    created_chapters += 1

                for lesson_data in lessons_data:
                    lesson, l_created = Lesson.objects.update_or_create(
                        slug=slugify(
                            f"{topic_data['title']}-{chapter_data['title']}-{lesson_data['title']}"
                        ),
                        defaults={
                            'chapter': chapter,
                            'title': lesson_data['title'],
                            'summary': lesson_data['summary'],
                            'content': lesson_data.get('content', ''),
                            'difficulty': lesson_data.get('difficulty', 'beginner'),
                            'featured': lesson_data.get('featured', False),
                            'order': lesson_data.get('order', 0),
                            'reading_time': lesson_data.get('reading_time', 5),
                            'is_published': True,
                        },
                    )
                    if l_created:
                        created_lessons += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seeding complete — '
            f'{created_topics} topic(s), '
            f'{created_chapters} chapter(s), '
            f'{created_lessons} lesson(s) created.'
        ))
