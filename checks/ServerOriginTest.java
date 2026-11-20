package org.jellyfin.mobile.webapp;

/** Runs against the actual patched policy, with no Android/JUnit dependency. */
public final class ServerOriginTest {
    public static void main(String[] args) {
        ServerOrigin origin = ServerOrigin.parse("https://media.example/jellyfin");
        String[] allowed = {
            "https://media.example/", "https://MEDIA.example:443/web/#/home",
            "HTTPS://media.example/image.jpg?x=1", "https://media.example/native/nativeshell.js"
        };
        String[] denied = {
            "http://media.example/", "https://media.example:80/", "https://media.example:8096/",
            "https://media.example.evil.test/", "https://evil.test/media.example",
            "https://media.example@evil.test/", "https://evil@media.example/",
            "//media.example/", "/web/", "about:blank", "about:srcdoc", "data:text/html,hi",
            "blob:https://media.example/id", "javascript:alert(1)", "file:///tmp/a",
            "intent://media.example/", "https://media.example:0/", "https://media.example:65536/",
            "https://media.example\\@evil.test/", "https://media.example/%zz", "https://media.example\n.evil/",
            "https://%6dedia.example/", "https://media.example./", "https://media.example:abc/"
        };
        for (String url : allowed) check(origin.allows(url), "Must allow " + url);
        for (String url : denied) check(!origin.allows(url), "Must deny " + url);
        check(ServerOrigin.parse("http://192.168.1.12:8096/").allows("http://192.168.1.12:8096/web/"), "LAN port");
        check(!ServerOrigin.parse("http://192.168.1.12:8096/").allows("http://192.168.1.12/"), "LAN default port");
        check(ServerOrigin.parse("https://[2001:db8::1]/").allows("https://[2001:db8::1]:443/web/"), "IPv6");
        check(ServerOrigin.parse("https://[2001:db8::1]/").getRule().equals("https://[2001:db8::1]:443"), "IPv6 rule");
        check(ServerOrigin.parse("data:hi") == null, "Invalid server");
        System.out.println("Origin policy: " + (allowed.length + denied.length + 5) + " checks passed");
    }

    private static void check(boolean result, String message) {
        if (!result) throw new AssertionError(message);
    }
}
