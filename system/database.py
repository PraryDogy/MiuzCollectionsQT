import sqlalchemy
from sqlalchemy import event

from cfg import Static

METADATA = sqlalchemy.MetaData()

HIST_BINS = (50, 60)
HIST_BYTES = HIST_BINS[0] * HIST_BINS[1]   # 3000 байт в uint8
DB_SCHEMA_VERSION = 3.1                       # 3 = name_key у thumbs, гистограммы uint8


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
	name_key = _table_thumbs.c.coll   # нормализованное имя без расширения
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
		cls.migrate_to_v3(Dbase.main_engine)
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

		@event.listens_for(engine, "connect")
		def _set_sqlite_pragmas(dbapi_conn, _):
			cursor = dbapi_conn.cursor()
			cursor.execute("PRAGMA foreign_keys=ON")
			cursor.close()

		return engine

	@classmethod
	def ensure_schema(cls, engine: sqlalchemy.Engine) -> None:
		"""Создаёт отсутствующие таблицы. Безопасно вызывать при каждом старте."""
		METADATA.create_all(engine)

	@classmethod
	def migrate_to_v3(cls, engine: sqlalchemy.Engine) -> None:

		"""При версии ниже DB_SCHEMA_VERSION очищает properties и заполняет name_key для всех thumbs."""
		with engine.begin() as conn:
			version = conn.execute(sqlalchemy.text("PRAGMA user_version")).scalar()
			if version >= DB_SCHEMA_VERSION:
				return

			from .utils import Utils  # нужен для Utils.make_name_key
			conn.execute(sqlalchemy.delete(Properties.table))

			rows = conn.execute(
				sqlalchemy.select(Thumbs.id, Thumbs.rel_img_path)
			).all()

			if rows:
				conn.execute(
					sqlalchemy.update(Thumbs.table)
					.where(Thumbs.id == sqlalchemy.bindparam("b_id"))
					.values({Thumbs.name_key.name: sqlalchemy.bindparam("b_key")}),
					[
						{"b_id": row_id, "b_key": Utils.make_name_key(rel_img_path)}
						for row_id, rel_img_path in rows
					],
				)

			conn.execute(sqlalchemy.text(f"PRAGMA user_version = {DB_SCHEMA_VERSION}"))
		# VACUUM вне транзакции: Dbase.vacuum использует AUTOCOMMIT
		cls.vacuum()

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