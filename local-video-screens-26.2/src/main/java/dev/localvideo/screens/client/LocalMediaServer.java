package dev.localvideo.screens.client;

import com.sun.net.httpserver.Headers;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.File;
import java.io.IOException;
import java.io.OutputStream;
import java.io.RandomAccessFile;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

final class LocalMediaServer implements AutoCloseable {
    private final File file;
    private final HttpServer server;
    private final ExecutorService executor;

    LocalMediaServer(File file) throws IOException {
        this.file = file.getCanonicalFile();
        this.server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        this.executor = Executors.newFixedThreadPool(2, r -> {
            Thread t = new Thread(r, "LocalVideoScreens-Media");
            t.setDaemon(true);
            return t;
        });
        server.setExecutor(executor);
        server.createContext("/player", this::servePlayer);
        server.createContext("/media", this::serveMedia);
        server.start();
    }

    String playerUrl() {
        return "http://127.0.0.1:" + server.getAddress().getPort() + "/player";
    }

    private void servePlayer(HttpExchange exchange) throws IOException {
        try {
            if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())
                    && !"HEAD".equalsIgnoreCase(exchange.getRequestMethod())) {
                exchange.sendResponseHeaders(405, -1);
                return;
            }

            String mediaMime = mimeType(file.getName());
            String safeName = escapeHtml(file.getName());
            byte[] html = ("""
                    <!doctype html>
                    <html>
                    <head>
                      <meta charset="utf-8">
                      <style>
                        html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#000;color:#fff;font-family:monospace}
                        video{position:fixed;inset:0;width:100%;height:100%;object-fit:contain;background:#000}
                        #diag{position:fixed;left:12px;top:12px;z-index:10;max-width:calc(100%% - 24px);
                              padding:8px 10px;background:rgba(0,0,0,.72);font-size:15px;line-height:1.35;
                              white-space:pre-wrap;pointer-events:none}
                      </style>
                    </head>
                    <body>
                      <video id="v" autoplay muted playsinline preload="auto" controls src="/media"></video>
                      <div id="diag">PLAYER PAGE LOADED
                    file: %s
                    mime: %s
                    bytes: %d
                    state: waiting for media...</div>
                      <script>
                        const v=document.getElementById('v');
                        const d=document.getElementById('diag');
                        const names={1:'MEDIA_ERR_ABORTED',2:'MEDIA_ERR_NETWORK',3:'MEDIA_ERR_DECODE',4:'MEDIA_ERR_SRC_NOT_SUPPORTED'};
                        const show=(msg)=>{
                          const err=v.error ? (names[v.error.code]||('MEDIA_ERROR_'+v.error.code)) : 'none';
                          d.textContent='PLAYER PAGE LOADED\n'
                            +'file: %s\n'
                            +'mime: %s\n'
                            +'state: '+msg+'\n'
                            +'readyState: '+v.readyState+' networkState: '+v.networkState+'\n'
                            +'error: '+err+'\n'
                            +'currentSrc: '+v.currentSrc;
                        };
                        ['loadstart','loadedmetadata','loadeddata','canplay','playing','pause','stalled','suspend','waiting','ended','emptied']
                          .forEach(e=>v.addEventListener(e,()=>show(e)));
                        v.addEventListener('error',()=>show('ERROR'));
                        const start=()=>{
                          show('play() requested');
                          v.play().then(()=>show('play() resolved')).catch(e=>show('play() rejected: '+e.name+': '+e.message));
                        };
                        v.addEventListener('loadeddata', start, {once:true});
                        v.addEventListener('canplay', start, {once:true});
                        start();
                      </script>
                    </body>
                    </html>
                    """).formatted(safeName, mediaMime, file.length(), safeName, mediaMime)
                    .getBytes(StandardCharsets.UTF_8);

            Headers h = exchange.getResponseHeaders();
            h.set("Content-Type", "text/html; charset=utf-8");
            h.set("Cache-Control", "no-store");
            if ("HEAD".equalsIgnoreCase(exchange.getRequestMethod())) {
                exchange.sendResponseHeaders(200, -1);
                return;
            }
            exchange.sendResponseHeaders(200, html.length);
            try (OutputStream out = exchange.getResponseBody()) {
                out.write(html);
            }
        } finally {
            exchange.close();
        }
    }

    private void serveMedia(HttpExchange exchange) throws IOException {
        try {
            String method = exchange.getRequestMethod();
            if (!"GET".equalsIgnoreCase(method) && !"HEAD".equalsIgnoreCase(method)) {
                exchange.sendResponseHeaders(405, -1);
                return;
            }
            if (!file.isFile()) {
                exchange.sendResponseHeaders(404, -1);
                return;
            }

            long length = file.length();
            long start = 0;
            long end = Math.max(0, length - 1);
            boolean partial = false;

            String range = exchange.getRequestHeaders().getFirst("Range");
            if (range != null && range.startsWith("bytes=")) {
                String spec = range.substring(6).split(",", 2)[0].trim();
                String[] parts = spec.split("-", 2);
                try {
                    if (!parts[0].isBlank()) {
                        start = Long.parseLong(parts[0]);
                    }
                    if (parts.length > 1 && !parts[1].isBlank()) {
                        end = Long.parseLong(parts[1]);
                    }
                    if (start < 0 || start >= length || end < start) {
                        exchange.getResponseHeaders().set("Content-Range", "bytes */" + length);
                        exchange.sendResponseHeaders(416, -1);
                        return;
                    }
                    end = Math.min(end, length - 1);
                    partial = true;
                } catch (NumberFormatException ignored) {
                    start = 0;
                    end = Math.max(0, length - 1);
                }
            }

            long count = length == 0 ? 0 : end - start + 1;
            Headers h = exchange.getResponseHeaders();
            h.set("Content-Type", mimeType(file.getName()));
            h.set("Accept-Ranges", "bytes");
            h.set("Cache-Control", "no-store");
            h.set("Content-Length", Long.toString(count));
            if (partial) {
                h.set("Content-Range", "bytes " + start + "-" + end + "/" + length);
            }

            int status = partial ? 206 : 200;
            if ("HEAD".equalsIgnoreCase(method)) {
                exchange.sendResponseHeaders(status, -1);
                return;
            }

            exchange.sendResponseHeaders(status, count);
            try (RandomAccessFile raf = new RandomAccessFile(file, "r");
                 OutputStream out = exchange.getResponseBody()) {
                raf.seek(start);
                byte[] buffer = new byte[128 * 1024];
                long remaining = count;
                while (remaining > 0) {
                    int read = raf.read(buffer, 0, (int) Math.min(buffer.length, remaining));
                    if (read < 0) break;
                    out.write(buffer, 0, read);
                    remaining -= read;
                }
            } catch (IOException ignored) {
                // Chromium may cancel an old range request after seeking.
            }
        } finally {
            exchange.close();
        }
    }

    private static String escapeHtml(String value) {
        return value.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\"", "&quot;");
    }

    private static String mimeType(String name) {
        String n = name.toLowerCase(Locale.ROOT);
        if (n.endsWith(".webm")) return "video/webm";
        if (n.endsWith(".m4v")) return "video/x-m4v";
        if (n.endsWith(".mov")) return "video/quicktime";
        if (n.endsWith(".mkv")) return "video/x-matroska";
        if (n.endsWith(".avi")) return "video/x-msvideo";
        return "video/mp4";
    }

    @Override
    public void close() {
        server.stop(0);
        executor.shutdownNow();
    }
}
