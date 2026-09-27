package com.furk5nn.videoscreen.client;

import de.keksuccino.rinku.Rinku;
import de.keksuccino.rinku.RinkuBrowser;
import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import net.minecraft.resources.Identifier;

public final class ChromiumVideoPlayer implements AutoCloseable {
    private final File source;
    private final Path htmlFile;
    private RinkuBrowser browser;
    private boolean paused;
    private int width;
    private int height;

    public ChromiumVideoPlayer(File source, int width, int height) throws IOException {
        this.source = source;
        this.htmlFile = Files.createTempFile("videoscreen-", ".html");

        String videoUri = source.toURI().toASCIIString()
            .replace("\\", "\\\\")
            .replace("'", "\\'");

        String html = """
            <!doctype html>
            <html>
            <head>
              <meta charset="utf-8">
              <style>
                html,body{margin:0;width:100%%;height:100%%;overflow:hidden;background:#000}
                video{display:block;width:100%%;height:100%%;object-fit:contain;background:#000}
              </style>
            </head>
            <body>
              <video id="v" autoplay loop controls playsinline></video>
              <script>
                const source='%s';
                const v=document.getElementById('v');
                let objectUrl=null;

                function startPlayback() {
                  v.loop=true;
                  v.volume=1.0;
                  v.play().catch(err => console.error('[VideoScreen] play failed', err));
                }

                function assignDirect() {
                  console.warn('[VideoScreen] Blob load failed, trying direct file source');
                  v.src=source;
                  v.load();
                  startPlayback();
                }

                function loadLocalVideo() {
                  const xhr=new XMLHttpRequest();
                  try {
                    xhr.open('GET', source, true);
                    xhr.responseType='blob';
                  } catch (e) {
                    console.error('[VideoScreen] XHR setup failed', e);
                    assignDirect();
                    return;
                  }

                  xhr.onload=function() {
                    if (xhr.status!==0 && xhr.status!==200) {
                      console.error('[VideoScreen] Local video XHR status', xhr.status);
                      assignDirect();
                      return;
                    }
                    try {
                      objectUrl=URL.createObjectURL(xhr.response);
                      v.src=objectUrl;
                      v.load();
                      startPlayback();
                    } catch (e) {
                      console.error('[VideoScreen] Blob URL failed', e);
                      assignDirect();
                    }
                  };

                  xhr.onerror=function() {
                    console.error('[VideoScreen] Local video XHR failed');
                    assignDirect();
                  };

                  xhr.send();
                }

                v.addEventListener('error', () => {
                  const e=v.error;
                  console.error('[VideoScreen] media error', e ? e.code : 'unknown', source);
                });

                window.addEventListener('pagehide', () => {
                  if (objectUrl) URL.revokeObjectURL(objectUrl);
                });

                loadLocalVideo();
              </script>
            </body>
            </html>
            """.formatted(videoUri);
        Files.writeString(htmlFile, html, StandardCharsets.UTF_8);

        if (!Rinku.isInitialized()) {
            throw new IllegalStateException("Rinku is not initialized yet");
        }

        this.width = Math.max(320, width);
        this.height = Math.max(180, height);
        browser = Rinku.createBrowser(htmlFile.toUri().toASCIIString(), false);
        browser.resize(this.width, this.height);
        browser.setFocus(false);
    }

    public void resize(int width, int height) {
        int newWidth = Math.max(320, width);
        int newHeight = Math.max(180, height);
        if (browser != null && (newWidth != this.width || newHeight != this.height)) {
            this.width = newWidth;
            this.height = newHeight;
            browser.resize(newWidth, newHeight);
        }
    }

    public boolean isReady() {
        return browser != null && browser.getTextureIdentifier() != null;
    }

    public Identifier texture() {
        return browser == null ? null : browser.getTextureIdentifier();
    }

    public void togglePause() {
        if (browser == null) return;
        paused = !paused;
        String js = paused
            ? "(()=>{const v=document.getElementById('v');if(v)v.pause();})()"
            : "(()=>{const v=document.getElementById('v');if(v)v.play().catch(()=>{});})()";
        browser.executeJavaScript(js, browser.getURL(), 0);
    }

    public boolean isPaused() {
        return paused;
    }

    public File source() {
        return source;
    }

    @Override
    public void close() {
        if (browser != null) {
            browser.close();
            browser = null;
        }
        try {
            Files.deleteIfExists(htmlFile);
        } catch (IOException ignored) {
        }
    }
}
