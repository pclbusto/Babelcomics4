import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from entidades import Base
from entidades.comicbook_info_cover_model import ComicbookInfoCover
from entidades.comicbook_info_model import ComicbookInfo
from entidades.volume_model import Volume
from repositories.setup_repository import SetupRepository
from helpers.thumbnail_path import initialize as init_thumbnail_path

# Config
DB_PATH = 'data/babelcomics.db'
IDS_TO_CHECK = [2, 5, 7, 9, 15, 17, 19, 21, 23, 25, 28, 30]

def debug_covers():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: DB not found at {DB_PATH}")
        return

    engine = create_engine(f'sqlite:///{DB_PATH}')
    Session = sessionmaker(bind=engine)
    session = Session()

    # Load config
    setup_repo = SetupRepository(session)
    config = setup_repo.obtener_o_crear_configuracion()
    custom_path = getattr(config, 'carpeta_thumbnails', None)
    print(f"Configured Thumbnails Path: {custom_path}")
    
    init_thumbnail_path(custom_path)

    print(f"Checking {len(IDS_TO_CHECK)} IDs...")
    print("-" * 60)

    for id_cover in IDS_TO_CHECK:
        cover = session.query(ComicbookInfoCover).get(id_cover)
        
        if not cover:
            print(f"ID {id_cover}: NOT FOUND in DB")
            continue
            
        print(f"ID {id_cover}:")
        print(f"  - URL Imagen (DB): '{cover.url_imagen}'")
        
        if not cover.url_imagen:
             print("  -> ERROR: url_imagen is empty/null")
        
        if cover.comic_info:
            print(f"  - Comic Hint: {cover.comic_info.titulo} #{cover.comic_info.numero}")
            if cover.comic_info.volume:
                print(f"  - Volume: {cover.comic_info.volume.nombre} (ID: {cover.comic_info.volume.id_volume})")
            else:
                 print("  -> ERROR: No Volume associated")
        else:
             print("  -> ERROR: No ComicInfo associated")
             
        # Check path calculation
        try:
            path = cover.obtener_ruta_local()
            print(f"  - Calculated Path: {path}")
            
            if "Comic_sin_caratula" in path:
                print("  -> RESULT: Returns Default Image (Failure)")
            elif os.path.exists(path):
                print("  -> RESULT: File Exists ✅")
            else:
                print("  -> RESULT: File DOES NOT Exist ❌")
                
        except Exception as e:
            print(f"  -> ERROR calculating path: {e}")
            
        print("-" * 60)
        
    session.close()

if __name__ == "__main__":
    debug_covers()
