pg_dump -U postgres -W -d zoom-medsenger-bot -h 127.0.0.1 > call_bot.sql
zip -r call.zip call_bot.sql
