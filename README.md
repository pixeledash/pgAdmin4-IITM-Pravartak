# Enhancement to pgAdmin 4

pgAdmin 4 is a web-based administration and management tool for PostgreSQL databases. It is the latest version of pgAdmin, redesigned from earlier desktop-based versions to provide a modern, flexible, and user-friendly interface for managing PostgreSQL servers.

## Implemented Features  

#### **1. Automated Backup Scheduler**  
- **Flexible Scheduling Options** – Supports **one-time, daily, weekly, and monthly** backup schedules.  
- **Dynamic Scheduling Logic** – Automatically determines the next backup execution time based on prior runs.  
- **Background Scheduler Service** – Operates as a separate thread to manage backup jobs efficiently without interfering with pgAdmin4 operations.  
- **Job Management & Validation** – Ensures accurate backup job configurations using **SQLAlchemy**.  
- **API Endpoints** – Provides **REST API endpoints** for scheduling status monitoring and restarting the scheduler.  

#### **2. ERD Export Tool Enhancements**  
- **Multi-Format Export Support** – Enables **PNG, JPEG, WebP, and PDF** export options.  
- **High-Resolution Export** – Allows users to generate **2x resolution** images for better clarity.  
- **Quality Control for Image Formats** – Adjustable compression settings for **JPEG and WebP** exports.  
- **Automatic Sizing** – Dynamically determines diagram dimensions to **ensure all elements are captured**.  
- **Consistent Background Rendering** – Ensures a **uniform white background** for exported images.  
- **PDF Generation** – Leverages **jsPDF** to convert ERD diagrams into properly formatted **PDF documents**.  

#### **3. Schema Diff Tool Enhancements**  
- **Color-Coded SQL Differences** –  
  - **Additions** → Highlighted in Green  
  - **Deletions** → Highlighted in Red  
  - **Modifications** → Highlighted in Yellow  
- **Copy-to-Clipboard Functionality** – Enables efficient copying of SQL differences for quick reference.  
- **PropTypes Validation** – Ensures proper data handling within **React components**.  
- **UI/UX Enhancements** – Improved layout and styling for better readability.  

## Installation

### Building the Runtime

To build the runtime, the following packages must be installed:

* NodeJS 16+
* Yarn

Change into the runtime directory, and run *yarn install*. This will install the
dependencies required.

In order to use the runtime in a development environment, you'll need to copy
*dev_config.json.in* file to *dev_config.json*, and edit the paths to the Python
executable and *pgAdmin.py* file, otherwise the runtime will use the default
paths it would expect to find in the standard package for your platform.

You can then execute the runtime by running something like:

```bash
yarn run start
```

### Configuring the Python Environment

In order to run the Python code, a suitable runtime environment is required.
Python version 3.7 and later are currently supported. It is recommended that a
Python Virtual Environment is setup for this purpose, rather than using the
system Python environment. On Linux and Mac systems, the process is fairly
simple - adapt as required for your distribution:

1. Create a virtual environment in an appropriate directory. The last argument is
   the name of the environment; that can be changed as desired:

   ```bash
   $ python3 -m venv venv
   ```

2. Now activate the virtual environment:

   ```bash
   $ source venv/bin/activate
   ```

3. Some of the components used by pgAdmin require a very recent version of *pip*,
   so update that to the latest:

   ```bash
   $ pip install --upgrade pip
   ```

4. Ensure that a PostgreSQL installation's bin/ directory is in the path (so
   pg_config can be found for building psycopg3), and install the required
   packages:

   ```bash
   (venv) $ PATH=$PATH:/usr/local/pgsql/bin pip install -r $PGADMIN4_SRC/requirements.txt
   ```

   If you are planning to run the regression tests, you also need to install
   additional requirements from web/regression/requirements.txt:

   ```bash
   (venv) $ pip install -r $PGADMIN4_SRC/web/regression/requirements.txt
   ```

5. Create a local configuration file for pgAdmin. Edit
   $PGADMIN4_SRC/web/config_local.py and add any desired configuration options
   (use the config.py file as a reference - any settings duplicated in
   config_local.py will override those in config.py). A typical development
   configuration may look like:

    ```python
    from config import *

    # Debug mode
    DEBUG = True

    # App mode
    SERVER_MODE = True

    # Enable the test module
    MODULE_BLACKLIST.remove('test')

    # Log
    CONSOLE_LOG_LEVEL = DEBUG
    FILE_LOG_LEVEL = DEBUG

    DEFAULT_SERVER = '127.0.0.1'

    UPGRADE_CHECK_ENABLED = True

    # Use a different config DB for each server mode.
    if SERVER_MODE == False:
        SQLITE_PATH = os.path.join(
            DATA_DIR,
            'pgadmin4-desktop.db'
        )
    else:
        SQLITE_PATH = os.path.join(
            DATA_DIR,
            'pgadmin4-server.db'
        )
   ```

   This configuration allows easy switching between server and desktop modes
   for testing.

6. The initial setup of the configuration database is interactive in server
   mode, and non-interactive in desktop mode. You can run it either by
   running:

   ```bash
   (venv) $ python3 $PGADMIN4_SRC/web/setup.py
   ```

   or by starting pgAdmin 4:

   ```bash
   (venv) $ python3 $PGADMIN4_SRC/web/pgAdmin4.py
   ```

   Whilst it is possible to automatically run setup in desktop mode by running
   the runtime, that will not work in server mode as the runtime doesn't allow
   command line interaction with the setup program.

At this point you will be able to run pgAdmin 4 from the command line in either
server or desktop mode, and access it from a web browser using the URL shown in
the terminal once pgAdmin has started up.

Setup of an environment on Windows is somewhat more complicated unfortunately,
please see *pkg/win32/README.txt* for complete details.

### Building the Web Assets

pgAdmin is dependent on a number of third party Javascript libraries. These,
along with it's own Javascript code, SCSS/CSS code and images must be
compiled into a "bundle" which is transferred to the browser for execution
and rendering. This is far more efficient than simply requesting each
asset as it's needed by the client.

To create the bundle, you will need the 'yarn' package management tool to be
installed. Then, you can run the following commands on a *nix system to
download the required packages and build the bundle:

```bash
(venv) $ cd $PGADMIN4_SRC
(venv) $ make install-node
(venv) $ make bundle
```

On Windows systems (where "make" is not available), the following commands
can be used:

```
C:\> cd $PGADMIN4_SRC\web
C:\$PGADMIN4_SRC\web> yarn install
C:\$PGADMIN4_SRC\web> yarn run bundle
```

### Building packages

Most packages can be built using the Makefile in $PGADMIN4_SRC, provided all
the setup and configuration above has been completed.

To build a source tarball:

```bash
(venv) $ make src
```

To build a PIP Wheel, activate either a Python 3 virtual environment, configured
with all the required packages, and then run:

```bash
(venv) $ make pip
```

To build the macOS AppBundle, please see *pkg/mac/README*.

To build the Windows installer, please see *pkg/win32/README.txt*.
### Create Database Migrations

In order to make changes to the SQLite DB, navigate to the 'web' directory:

```bash
(venv) $ cd $PGADMIN4_SRC/web
```

Create a migration file with the following command:

```bash
(venv) $ FLASK_APP=pgAdmin4.py flask db revision
```

This will create a file in: $PGADMIN4_SRC/web/migrations/versions/ .
Add any changes to the 'upgrade' function.
Increment the SCHEMA_VERSION in $PGADMIN4_SRC/web/pgadmin/model/__init__.py file.

There is no need to increment the SETTINGS_SCHEMA_VERSION.

## Implementation
