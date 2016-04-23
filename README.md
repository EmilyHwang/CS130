# Beehive - Social media analytics for everyone
##### UCLA CS 130, Spring 2016

## Setup
1.) First, make sure you have `virtualenv` installed:
```
$ pip install virtualenv
```

2.) Then change into the `/CS130/beehive` folder to create a virtual environment for Beehive:
```
$ cd CS130/beehive
$ virtualenv venv
```

You should now have a `venv` folder inside the `beehive` folder. Make sure that your virtual environment uses Python 2.7 (you will see the Python version when this line is output `New python executable in...`). If not, remove the `venv` folder and use Python 2.7:

```
$ virtualenv -p /usr/bin/python2.7 venv
```

3.) To begin using the virtual environment, activate it:
```
source venv/bin/activate
```

4.) Install packages and dependencies needed for Beehive:
```
pip install -r requirements.txt
```

5.) Now Beehive is ready to be run.
```
cd app
python beehive.py
```

6.) When you are done working in the virtual environment, deactivate it:
```
deactivate
```

7.) If you install any new packages, please make sure to do a:
```
pip freeze > requirements.txt
```

## Running Beehive
You only need to do the setup once. Subsequently, to run Beehive, the workflow is as follows:

1. While in the `CS130/beehive` directory, activate the virtual environment: `source venv/bin/activate`

2. Make edits/work on code/run Beehive: `python beehive.py`

3. Deactivatr virtual environment: `deactivate`
