from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/"data"; LOGS=ROOT/"logs"
STATE_FILE=DATA/"operations.json"; LOG_FILE=LOGS/"organizer.log"
CATEGORIES={
"Images":{'.png','.jpg','.jpeg','.gif','.bmp','.webp','.tiff','.svg','.heic'},
"Documents":{'.pdf','.doc','.docx','.odt','.rtf','.txt','.md','.tex'},
"Spreadsheets":{'.csv','.xls','.xlsx','.ods'},
"Presentations":{'.ppt','.pptx','.odp','.key'},
"Videos":{'.mp4','.mkv','.mov','.avi','.webm','.wmv','.m4v'},
"Audio":{'.mp3','.wav','.flac','.aac','.ogg','.m4a','.wma'},
"Archives":{'.zip','.rar','.7z','.tar','.gz','.bz2','.xz'},
"Code":{'.py','.js','.ts','.html','.css','.php','.java','.c','.cpp','.h','.sql','.json','.xml','.yml','.yaml','.sh','.bat'},
"Installers":{'.exe','.msi','.dmg','.pkg','.deb','.rpm','.apk'},
"Fonts":{'.ttf','.otf','.woff','.woff2'}}
