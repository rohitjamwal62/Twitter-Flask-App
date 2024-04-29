# Flask Application Setup

## Prerequisites

- Python 3.x installed on your system. Verify with:

  ```
  python3 --version
  ```

  Ensure the version starts with 3.

## Setup Instructions

**Step 1: Navigate to the Project Directory**

In your terminal, navigate to the directory where your project is located. For example:

```
cd path/to/your/project
```

**Step 2: Activate the Virtual Environment**

For an existing 'venv' folder:

```
source venv/bin/activate
```

On Windows:

```
.\venv\Scripts\activate
```

If 'venv' is not present, proceed:

**Step 3: Create and Activate Virtual Environment**

```
python3 -m venv venv
```

On Windows:

```
py -m venv venv
```

Activate the virtual environment:

```
source venv/bin/activate
```

On Windows:

```
.\venv\Scripts\activate
```

**Step 4: Run the Application**

```
python3 app.py
```

Or:

```
python app.py
```

Your Flask application should be running.

Now, whether 'venv' is present or not, you have the steps to set up and run your Flask application.
