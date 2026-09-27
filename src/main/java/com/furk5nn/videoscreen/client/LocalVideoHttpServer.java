package com.furk5nn.videoscreen.client;

import com.sun.net.httpserver.Headers;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.File;
import java.io.IOException;
import java.io.OutputStream;
import java.io.RandomAccessFile;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.URI;
import java.util.UUID;
import java.util.concurrent.Executors;

final class LocalVideoHttpServer implements AutoCloseable {
    private static final int BUFFER_SIZE = 64 * 1024;

    private final File file;
    private final HttpServer server;
    private final String token;
    private final URI uri;

    LocalVideoHttpServer(File file) throws IOException {
        this.file = file.getCanonicalFile();
        this.token = UUID.randomUUID().toString().replace("-", "");

        InetAddress loopback = InetAddress.getByName("127.0.0.1");
        this.server = HttpServer.create(new InetSocketAddress(loopback, 0), 0);
        this.server.createContext("/" + token, this::handle);
        this.server.setExecutor(Executors.newSingleThreadExecutor(r -> {
            Thread t = new Thread(r, "VideoScreen-LocalHttp");
            t.setDaemon(true);
            return t;
        }));
        this.server.start();

        int port = this.server.getAddress().getPort();
        this.uri = URI.create("http://127.0.0.1:" + port + "/" + token);
    }

    URI uri() {
        return uri;
    }

    private void handle(HttpExchange exchange) throws IOException {
        try {
            String method = exchange.getRequestMethod();
            if (!"GET".equalsIgnoreCase(method) && !"HEAD".equalsIgnoreCase(method)) {
                exchange.sendResponseHeaders(405, -1);
                return;
            }

            long length = file.length();
            long start = 0;
            long end = Math.max(0, length - 1);
            boolean partial = false;

            String range = exchange.getRequestHeaders().getFirst("Range");
            if (range != null && range.startsWith("bytes=")) {
                String spec = range.substring("bytes=".length()).trim();
                int dash = spec.indexOf('-');
                if (dash >= 0) {
                    String a = spec.substring(0, dash).trim();
                    String b = spec.substring(dash + 1).trim();
                    try {
                        if (!a.isEmpty()) start = Long.parseLong(a);
                        if (!b.isEmpty()) end = Long.parseLong(b);
                        else end = length - 1;
                        if (start < 0 || start >= length) {
                            exchange.getResponseHeaders().set("Content-Range", "bytes */" + length);
                            exchange.sendResponseHeaders(416, -1);
                            return;
                        }
                        if (end >= length) end = length - 1;
                        if (end < start) end = start;
                        partial = true;
                    } catch (NumberFormatException ignored) {
                    }
                }
            }

            long contentLength = length == 0 ? 0 : (end - start + 1);
            Headers h = exchange.getResponseHeaders();
            h.set("Content-Type", "video/mp4");
            h.set("Accept-Ranges", "bytes");
            h.set("Cache-Control", "no-store");
            h.set("Access-Control-Allow-Origin", "*");
            if (partial) {
                h.set("Content-Range", "bytes " + start + "-" + end + "/" + length);
            }

            int status = partial ? 206 : 200;
            if ("HEAD".equalsIgnoreCase(method)) {
                h.set("Content-Length", Long.toString(contentLength));
                exchange.sendResponseHeaders(status, -1);
                return;
            }

            exchange.sendResponseHeaders(status, contentLength);
            try (RandomAccessFile raf = new RandomAccessFile(file, "r");
                 OutputStream out = exchange.getResponseBody()) {
                raf.seek(start);
                byte[] buffer = new byte[BUFFER_SIZE];
                long remaining = contentLength;
                while (remaining > 0) {
                    int read = raf.read(buffer, 0, (int) Math.min(buffer.length, remaining));
                    if (read < 0) break;
                    out.write(buffer, 0, read);
                    remaining -= read;
                }
            }
        } finally {
            exchange.close();
        }
    }

    @Override
    public void close() {
        server.stop(0);
    }
}
