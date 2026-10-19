# AMYCarousel standalone launcher (pywebview + PyInstaller)
# Emulates the window.electronAPI contract that AMYCarousel.htm already supports.
import json
import os
import sys
import webbrowser
from pathlib import Path

import webview

APP_NAME = "AMYCarousel"
HTML_FILE = "AMYCarousel.htm"


def resource_path(rel: str) -> Path:
    """Resolve a bundled resource both in dev and inside a PyInstaller bundle."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / rel


def data_dir() -> Path:
    """Per-user writable folder used to persist the app state."""
    root = os.environ.get("APPDATA") or str(Path.home() / ".config")
    d = Path(root) / APP_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


# JS shim injected before the page scripts: maps electronAPI -> pywebview API.
# The page checks window.electronAPI synchronously at startup, so it must exist early.
SHIM = r"""<script>
(function () {
  var ready = new Promise(function (resolve) {
    if (window.pywebview && window.pywebview.api) resolve();
    else window.addEventListener('pywebviewready', function () { resolve(); });
  });
  function call(name) {
    var args = Array.prototype.slice.call(arguments, 1);
    return ready.then(function () { return window.pywebview.api[name].apply(null, args); });
  }
  window.electronAPI = {
    loadState:    function ()  { return call('load_state'); },
    persistState: function (s) { return call('persist_state', s); },
    saveHtml:     function (s) { return call('save_html', s); },
    saveJson:     function (s) { return call('save_json', s); },
    openJson:     function ()  { return call('open_json'); }
  };
  // Open external http(s) links (target=_blank) in the default browser
  document.addEventListener('click', function (e) {
    var a = e.target.closest ? e.target.closest('a[href]') : null;
    if (!a || a.target !== '_blank' || !/^https?:\/\//i.test(a.href)) return;
    e.preventDefault();
    call('open_url', a.href);
  });
})();
</script>"""


class Api:
    """Methods exposed to JS. Keep the window private (underscore) so it is not exposed."""

    def __init__(self):
        self._window = None
        self._state_file = data_dir() / "state.json"

    # ---- helpers ----
    def _save_dialog(self, filename, ext_filter):
        # Support both new (FileDialog enum) and old (SAVE_DIALOG) pywebview versions
        dlg = getattr(getattr(webview, "FileDialog", None), "SAVE", None) or webview.SAVE_DIALOG
        res = self._window.create_file_dialog(
            dlg, save_filename=filename, file_types=(ext_filter, "All files (*.*)")
        )
        if not res:
            return None
        return res if isinstance(res, str) else res[0]

    def _write(self, path, text):
        Path(path).write_text(text, encoding="utf-8")
        return {"ok": True, "path": str(path)}

    # ---- electronAPI equivalents ----
    def load_state(self):
        # Must always return ok=True: the page builds its UI only in that case
        try:
            if self._state_file.exists():
                return {"ok": True, "content": self._state_file.read_text(encoding="utf-8")}
        except Exception:
            pass
        return {"ok": True, "content": "{}"}

    def persist_state(self, content):
        try:
            json.loads(content)  # validate before overwriting the saved state
            tmp = self._state_file.with_suffix(".tmp")
            tmp.write_text(content, encoding="utf-8")
            tmp.replace(self._state_file)  # atomic replace
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def save_html(self, content):
        try:
            path = self._save_dialog("carousel_output.html", "HTML files (*.html)")
            if not path:
                return {"ok": False, "error": "Cancelled"}
            return self._write(path, content)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def save_json(self, content):
        try:
            path = self._save_dialog("amycarousel_data.json", "JSON files (*.json)")
            if not path:
                return {"ok": False, "error": "Cancelled"}
            return self._write(path, content)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def open_url(self, url):
        # Only http(s) URLs are opened, in the system default browser
        if isinstance(url, str) and url.lower().startswith(("http://", "https://")):
            webbrowser.open(url)
            return {"ok": True}
        return {"ok": False}

    def open_json(self):
        try:
            dlg = getattr(getattr(webview, "FileDialog", None), "OPEN", None) or webview.OPEN_DIALOG
            res = self._window.create_file_dialog(
                dlg, allow_multiple=False, file_types=("JSON files (*.json)", "All files (*.*)")
            )
            if not res:
                return {"ok": False}  # cancelled: no error message shown
            path = res if isinstance(res, str) else res[0]
            return {"ok": True, "content": Path(path).read_text(encoding="utf-8")}
        except Exception as e:
            return {"ok": False, "error": str(e)}


def main():
    html = resource_path(HTML_FILE).read_text(encoding="utf-8")
    # Inject the shim right after <head> so it runs before the page scripts
    html = html.replace("<head>", "<head>" + SHIM, 1)

    api = Api()
    window = webview.create_window(
        "AMYCarousel", html=html, js_api=api, width=1400, height=900, min_size=(1000, 700)
    )
    api._window = window
    webview.start()


if __name__ == "__main__":
    main()
