from pathlib import Path

import uvicorn

from app.core import config

if __name__ == "__main__":
    project_dir: Path = Path(__file__).parent.parent
    reload_dirs = [str(project_dir.joinpath("./app")), str(project_dir.joinpath("./criaparse"))]

    uvicorn.run(
        app="app.core:app",
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=config.APP_MODE == config.AppMode.TESTING,
        reload_dirs=reload_dirs,
        workers=1,
    )
