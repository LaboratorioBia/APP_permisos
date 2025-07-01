import sqlalchemy
import os
import environ
from pathlib import Path

env = environ.Env()
environ.Env.read_env()

def conection_elemental():
    variables = os.environ.get("CON_ELEMENTAL").split(",")
    conection = sqlalchemy.create_engine(
        "mssql+pyodbc://%s:%s@%s/%s?driver=%s" 
        % (variables[0], variables[1], variables[2], variables[3], variables[4]))
    conection=conection.connect()
    return conection

def conection_house():
    # variables = os.environ.get("CON_HOUSE").split(",")
    conection = sqlalchemy.create_engine(
        "mssql+pyodbc://%s:%s@%s/%s?driver=%s" 
        # % (variables[0], variables[1], variables[2], variables[3], variables[4]))
        % (env.str("SQL_USER_DATABASE"), env.str("SQL_PASSWORD_DATABASE"), env.str("SQL_HOST"), env.str("SQL_NAME_DATABASE"), env.str("SQL_DRIVER")))
    conection=conection.connect()
    return conection

def conection_repocosmeticos():
    variables = os.environ.get("CON_REPO").split(",")
    conection = sqlalchemy.create_engine(
        "mssql+pyodbc://%s:%s@%s/%s?driver=%s" 
        % (variables[0], variables[1], variables[2], variables[3], variables[4]))
    conection=conection.connect()
    return conection

def conection_labelview():
    variables = os.environ.get("CON_LABEL").split(",")
    conection = sqlalchemy.create_engine(
        "mssql+pyodbc://%s:%s@%s/%s?driver=%s" 
        % (variables[0], variables[1], variables[2], variables[3], variables[4]))
    conection=conection.connect()
    return conection

def conection_rotulos():
    variables = os.environ.get("CON_ROTULOS").split(",")
    conection = sqlalchemy.create_engine(
        "mssql+pyodbc://%s:%s@%s/%s?driver=%s" 
        % (variables[0], variables[1], variables[2], variables[3], variables[4]))
    conection=conection.connect()
    return conection