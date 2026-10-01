from connection import connection


async def add_note(tg_id, username, title, content):
	conn = await connection()
	if conn is None:
		return None

	try:
		await conn.execute('''
		INSERT INTO users(tg_id,username) values($1,$2)
		on conflict(tg_id) do update set username=excluded.username
		''', tg_id, username)
		note_id = await conn.fetchval('''
		insert into notes(tg_id,title,content) values($1,$2,$3)
		returning id
		''', tg_id, title, content)
		print('Add notes succesfull')
		return note_id
	except Exception as error:
		print(f'Error in Add Note:{error}')
		return None
	finally:
		await conn.close()


async def show_notes(tg_id):
	conn = await connection()
	if conn is None:
		return None

	try:
		notes = await conn.fetch('''
		select id,title,content,created_at from notes
		where tg_id=$1 order by id desc
		''', tg_id)
		return notes
	except Exception as error:
		print(f'Error in show Note:{error}')
		return None
	finally:
		await conn.close()


async def get_note(note_id, tg_id):
	conn = await connection()
	if conn is None:
		return None

	try:
		note = await conn.fetchrow('''
		select id,title,content,created_at from notes
		where id=$1 and tg_id=$2
		''', note_id, tg_id)
		return note
	except Exception as error:
		print(f'Eror in get note:{error}')
		return None
	finally:
		await conn.close()


async def edit_note(note_id, tg_id, content):
	conn = await connection()
	if conn is None:
		return False
	try:
		result = await conn.execute('''
		update notes set content=$1 where id=$2 and tg_id=$3
		''', content, note_id, tg_id)
		return result == 'UPDATE 1'
	except Exception as error:
		print(f'Error in Update Note:{error}')
		return False
	finally:
		await conn.close()


async def delete_note(note_id, tg_id):
	conn = await connection()
	if conn is None:
		return False

	try:
		result = await conn.execute('''
		delete from notes where id=$1 and tg_id=$2
		''', note_id, tg_id)
		return result == 'DELETE 1'
	except Exception as error:
		print(f'Error in Dalete Note:{error}')
		return False
	finally:
		await conn.close()
