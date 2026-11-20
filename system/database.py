import sqlalchemy

from cfg import Static

METADATA = sqlalchemy.MetaData()

HIST_BINS = (50, 60)
HIST_BYTES = HIST_BINS[0] * HIST_BINS[1]   # 3000 байт в uint8
DB_SCHEMA_VERSION = 2                       # 2 = гистограммы uint8


_table_thumbs = sqlalchemy.Table(
	"thumbs", METADATA,
	sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
	sqlalchemy.Column("short_src", sqlalchemy.Text),
	sqlalchemy.Column("short_hash", sqlalchemy.Text),
	sqlalchemy.Column("size", sqlalchemy.Integer),
	sqlalchemy.Column("birth", sqlalchemy.Integer),
	sqlalchemy.Column("mod", sqlalchemy.Integer),
	sqlalchemy.Column("resol", sqlalchemy.Text),
	sqlalchemy.Column("coll", sqlalchemy.Text),
	sqlalchemy.Column("fav", sqlalchemy.Integer),
	sqlalchemy.Column("brand", sqlalchemy.Text),
)


class Thumbs:

	table = _table_thumbs
	id = _table_thumbs.c.id
	rel_img_path = _table_thumbs.c.short_src
	rel_thumb_path = _table_thumbs.c.short_hash
	size = _table_thumbs.c.size
	birth = _table_thumbs.c.birth
	mod = _table_thumbs.c.mod
	root = _table_thumbs.c.resol
	coll = _table_thumbs.c.coll
	fav = _table_thumbs.c.fav
	mf_alias = _table_thumbs.c.brand


_table_dirs = sqlalchemy.Table(
	"dirs", METADATA,
	sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
	sqlalchemy.Column("short_src", sqlalchemy.Text),
	sqlalchemy.Column("mod", sqlalchemy.Integer),
	sqlalchemy.Column("brand", sqlalchemy.Text),
)


class Dirs:
	"""
	Класс-обёртка для колонок таблицы `dirs` в базе данных.
	Предоставляет удобный доступ к колонкам через атрибуты класса.
	"""
	table = _table_dirs
	id = _table_dirs.c.id
	rel_dir_path = _table_dirs.c.short_src
	mod = _table_dirs.c.mod
	mf_alias = _table_dirs.c.brand

	@classmethod
	def reset_mod(cls, mf_alias: str):
		"""
		Сбрасывает mod всех папок Mf в 0, чтобы сканер при следующем запуске
		сравнил содержимое каждой папки, а не пропустил её по совпадению mtime.
		"""
		with Dbase.main_engine.begin() as conn:
			stmt = (
				sqlalchemy.update(cls.table)
				.where(cls.mf_alias == mf_alias)
				.values({cls.mod.name: 0})
			)
			conn.execute(stmt)


_table_properties = sqlalchemy.Table(
	"properties", METADATA,
	sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
	sqlalchemy.Column(
		"thumb_id",
		sqlalchemy.Integer,
		sqlalchemy.ForeignKey("thumbs.id", ondelete="CASCADE"),
		nullable=False
	),
	sqlalchemy.Column("bytes_hist", sqlalchemy.BLOB)
)


class Properties:
	table = _table_properties
	id = _table_properties.c.id
	thumb_id = _table_properties.c.thumb_id
	bytes_hist = _table_properties.c.bytes_hist


class Dbase:
	main_engine: sqlalchemy.Engine = None
	_timeout = 5
	_echo = False
	_same_thread = False
	WAL_ = None

	@classmethod
	def init(cls) -> sqlalchemy.Engine:
		Dbase.main_engine = cls.create_engine()
		cls.ensure_schema(Dbase.main_engine)
		cls.ensure_triggers(Dbase.main_engine)
		cls.migrate_histograms(Dbase.main_engine)
		cls.cleanup_orphan_properties(Dbase.main_engine)
		cls.toggle_wal(False)

	@classmethod
	def create_engine(cls):
		if not Static.DB_FILE.exists():
			raise Exception("Нет пользовательского файла DB_FILE")

		engine = sqlalchemy.create_engine(
			f"sqlite:///{Static.DB_FILE}",
			echo=cls._echo,
			connect_args={
				"check_same_thread": cls._same_thread,
				"timeout": cls._timeout,
			},
		)
		return engine

	@classmethod
	def ensure_schema(cls, engine: sqlalchemy.Engine) -> None:
		"""Создаёт недостающие таблицы и индексы. Безопасно вызывать при каждом старте."""
		METADATA.create_all(engine)  # создаёт только отсутствующие таблицы
		with engine.begin() as conn:
			conn.execute(sqlalchemy.text(
				"CREATE INDEX IF NOT EXISTS ix_properties_thumb_id ON properties(thumb_id)"
			))

	@classmethod
	def ensure_triggers(cls, engine: sqlalchemy.Engine) -> None:
		"""Триггеры пересоздаются при каждом старте, чтобы тела были актуальны."""
		with engine.begin() as conn:
			conn.execute(sqlalchemy.text("DROP TRIGGER IF EXISTS thumbs_delete_properties"))
			conn.execute(sqlalchemy.text("""
				CREATE TRIGGER thumbs_delete_properties
				AFTER DELETE ON thumbs
				BEGIN
					DELETE FROM properties WHERE thumb_id = OLD.id;
				END
			"""))
			conn.execute(sqlalchemy.text("DROP TRIGGER IF EXISTS properties_size_guard"))
			conn.execute(sqlalchemy.text(f"""
				CREATE TRIGGER properties_size_guard
				BEFORE INSERT ON properties
				WHEN NEW.bytes_hist IS NOT NULL AND LENGTH(NEW.bytes_hist) != {HIST_BYTES}
				BEGIN
					SELECT RAISE(IGNORE);
				END
			"""))

	@classmethod
	def migrate_histograms(cls, engine: sqlalchemy.Engine) -> None:
		"""Один раз удаляет гистограммы старого формата и освобождает место."""
		with engine.begin() as conn:
			version = conn.execute(sqlalchemy.text("PRAGMA user_version")).scalar()
			if version >= DB_SCHEMA_VERSION:
				return
			conn.execute(
				sqlalchemy.text("DELETE FROM properties WHERE LENGTH(bytes_hist) != :size"),
				{"size": HIST_BYTES},
			)
			conn.execute(sqlalchemy.text(f"PRAGMA user_version = {DB_SCHEMA_VERSION}"))
		# VACUUM вне транзакции: Dbase.vacuum использует AUTOCOMMIT
		cls.vacuum()

	@classmethod
	def cleanup_orphan_properties(cls, engine: sqlalchemy.Engine) -> None:
		with engine.begin() as conn:
			conn.execute(sqlalchemy.text(
				"DELETE FROM properties WHERE thumb_id NOT IN (SELECT id FROM thumbs)"
			))

	@classmethod
	def toggle_wal(cls, value: bool):
		conn = Dbase.main_engine.connect()
		if value:
			conn.execute(sqlalchemy.text("PRAGMA journal_mode=WAL"))
			cls.WAL_ = True
		else:
			conn.execute(sqlalchemy.text("PRAGMA journal_mode=DELETE"))
			cls.WAL_ = False
		conn.close()

	@classmethod
	def vacuum(cls):
		try:
			# AUTOCOMMIT, чтобы SQLite не открывал транзакцию неявно
			with cls.main_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
				conn.execute(sqlalchemy.text("VACUUM"))
		except Exception as e:
			print("database vacuum error", e)

	@classmethod
	def clear_root_mf(cls):
		...