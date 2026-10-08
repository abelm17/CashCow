const memory = new Map();

export function readStoredValue(key) {
    if (memory.has(key)) return memory.get(key);
    try {
        return window.localStorage.getItem(key);
    } catch {
        return null;
    }
}

export function writeStoredValue(key, value) {
    memory.set(key, value);
    try {
        window.localStorage.setItem(key, value);
    } catch {
        // Keep the user's choice for this page even when persistence is blocked.
    }
}

export function removeStoredValue(key) {
    memory.set(key, null);
    try {
        window.localStorage.removeItem(key);
    } catch {
        // The in-memory tombstone prevents an old token from being reused.
    }
}
