from django.core.management.base import BaseCommand, CommandError

import dotenv

class Command(BaseCommand):
    help = 'Sets up environment for the client'

    def handle(self, *args, **options):
        API_KEY = input("Enter API KEY: ")
        API_SECRET = input("Enter API SECRET: ")
        BRICK_SIZE = input("Enter BRICK SIZE: ")
        BRICK_REVERSAL = input("Enter BRICK REVERSAL: ")
        TIMEFRAME = input("Enter TIMEFRAME: ")
        EXCHANGE = input("Enter EXCHANGE: ")
        CONTRACT = input("Enter CONTRACT: ")
        FLAG = 0
        with open('.env', 'w') as fp:
            fp.write('')
        dotenv.set_key(dotenv.find_dotenv(), 'API_KEY', API_KEY)
        dotenv.set_key(dotenv.find_dotenv(), 'API_SECRET', API_SECRET)
        dotenv.set_key(dotenv.find_dotenv(), 'BRICK_SIZE', BRICK_SIZE)
        dotenv.set_key(dotenv.find_dotenv(), 'BRICK_REVERSAL', BRICK_REVERSAL)
        dotenv.set_key(dotenv.find_dotenv(), 'TIMEFRAME', TIMEFRAME)
        dotenv.set_key(dotenv.find_dotenv(), 'EXCHANGE', EXCHANGE)
        dotenv.set_key(dotenv.find_dotenv(), 'CONTRACT', CONTRACT)
        dotenv.set_key(dotenv.find_dotenv(), 'FLAG', str(FLAG))
        
        self.stdout.write(self.style.SUCCESS('Successfully created .env file'))            