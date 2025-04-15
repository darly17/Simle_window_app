from controller import Controller
from model import Database
from view import *

if __name__ == "__main__":
    database=Database()
    controller=Controller(database)
    viewer=Main(controller)
    