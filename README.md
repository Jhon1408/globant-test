# Globant test weather API instalation

The next instalation process it's meant for a Ubuntu 20 system with python 3.8 or higher.

## 1. Project instalation

First clone the repository.

```shell
$ git clone https://github.com/Jhon1408/globant-test.git
```

### Install the virtual enviroment

```shell
$ python -m venv env-globant
```

### Install python dependencies in the enviroment

First activate the virtual enviroment 

```shell
$ source env-globant/bin/activate
```

Then go inside the project folder and install the requirements

```shell
$ cd globant-test/
$ pip install -r requirements.txt
```

### Create the enviroment variables file

Inside the project folder create the .env

```shell
$ touch .env
```

And inside the file place the current variables

```txt
OPEN_WEATHER_MAP_URL=http://api.openweathermap.org/data/2.5
OPEN_WEATHER_MAP_ID=1508a9a4840a5574c822d70ca2132032
DEBUG=True
SECRET_KEY=django-insecure-_^!-s&le+w_@@a^p+ifvmysb!^g9tplopqkqwm3&1g^rlr%2wx
DJANGO_SETTINGS_MODULE=globant_test.settings
```

## 2. Testing the project

To test the project use the pytest.ini file

```shell
$ export DJANGO_SETTINGS_MODULE=globant_test.settings
$ pytest
```

## 3. Runing the project

To start the project run

```shell
$ python manage.py runserver
```

or

```shell
$ ./manage.py runserver
```

Now you can access the local server in the default port

```url
http://localhost:8000/api/
```

Testing the weather api

```url
http://localhost:8000/api/weather?city=Bogota&country=co
```
