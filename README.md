Bottle-based simple static file paste server.

* Highlighting done via `highlight` (http://www.andre-simon.de/)

* Password protected submission and deletion (weak, md5), viewing public

* Three interfaces:
    1) HTML form located at /
    2) Simple form located at /cmd
    3) Easy command line pasting via ./paste_via_curl.sh

* All dependencies are contained here, bootstrap and jquery.
* All pastes are kept in pastes/PASTE-* directories
* Can run as a module via `python2 -m paste_bottle` or ./run_paste_server.sh

