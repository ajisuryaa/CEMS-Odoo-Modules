/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useEffect, useRef, useState } from "@odoo/owl";
import { loadCSS, loadJS } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { _t } from "@web/core/l10n/translation";

const DEFAULT_LAT = 1.05;
const DEFAULT_LNG = 104.03;
const DEFAULT_RADIUS = 200;
const DEFAULT_ZOOM = 16;
const MIN_SIZE = 40;
const ICON_PATH = "/construction_progress/static/lib/leaflet/images";
const LEAFLET_JS = "/construction_progress/static/lib/leaflet/leaflet.js";
const LEAFLET_CSS = "/construction_progress/static/lib/leaflet/leaflet.css";

let leafletLoader = null;

function toFiniteNumber(value, fallback) {
    const num = typeof value === "number" ? value : parseFloat(value);
    return Number.isFinite(num) ? num : fallback;
}

function ensureLeaflet() {
    if (window.L) {
        return Promise.resolve(window.L);
    }
    if (!leafletLoader) {
        leafletLoader = Promise.all([loadCSS(LEAFLET_CSS), loadJS(LEAFLET_JS)]).then(() => {
            if (!window.L) {
                throw new Error("Leaflet loaded but window.L is missing");
            }
            return window.L;
        });
    }
    return leafletLoader;
}

function isElementReady(el) {
    if (!el) {
        return false;
    }
    const style = window.getComputedStyle(el);
    if (style.display === "none" || style.visibility === "hidden") {
        return false;
    }
    // Hidden notebook tabs collapse layout to 0.
    if (el.clientWidth < MIN_SIZE || el.clientHeight < MIN_SIZE) {
        return false;
    }
    const pane = el.closest(".tab-pane");
    if (pane && !pane.classList.contains("active") && !pane.classList.contains("show")) {
        return false;
    }
    return true;
}

export class CemsGeofenceMapField extends Component {
    static template = "construction_progress.CemsGeofenceMapField";
    static props = {
        ...standardFieldProps,
        latField: { type: String, optional: true },
        lngField: { type: String, optional: true },
        radiusField: { type: String, optional: true },
    };
    static defaultProps = {
        latField: "geofence_latitude",
        lngField: "geofence_longitude",
        radiusField: "geofence_radius",
    };

    setup() {
        this.mapRef = useRef("map");
        this.map = null;
        this.marker = null;
        this.circle = null;
        this.resizeObserver = null;
        this.intersectionObserver = null;
        this._tabListener = null;
        this._tabPane = null;
        this._tabTrigger = null;
        this._pollTimer = null;
        this._updatingFromMap = false;
        this._destroyed = false;
        this._initStarted = false;
        this.state = useState({
            radiusInput: this._radiusFromRecord(),
            loadError: "",
        });

        onMounted(() => {
            this._bootstrapMap();
        });
        onWillUnmount(() => {
            this._destroyed = true;
            this._teardown();
        });

        useEffect(
            () => {
                if (!this.map || this._updatingFromMap) {
                    return;
                }
                this.state.radiusInput = this._radiusFromRecord();
                this._syncFromRecord();
            },
            () => [
                this.props.record.data[this.props.latField],
                this.props.record.data[this.props.lngField],
                this.props.record.data[this.props.radiusField],
                this.props.readonly,
            ]
        );
    }

    get lat() {
        return toFiniteNumber(this.props.record.data[this.props.latField], 0);
    }

    get lng() {
        return toFiniteNumber(this.props.record.data[this.props.lngField], 0);
    }

    get radius() {
        return this._radiusFromRecord();
    }

    get hasCenter() {
        return Boolean(this.lat || this.lng);
    }

    get centerLat() {
        return this.hasCenter ? this.lat : DEFAULT_LAT;
    }

    get centerLng() {
        return this.hasCenter ? this.lng : DEFAULT_LNG;
    }

    get hintText() {
        if (this.state.loadError) {
            return this.state.loadError;
        }
        if (this.props.readonly) {
            return _t("Geofence preview (read only)");
        }
        return _t("Click the map or drag the marker to set the site center. Adjust radius below.");
    }

    _radiusFromRecord() {
        const value = toFiniteNumber(
            this.props.record.data[this.props.radiusField],
            DEFAULT_RADIUS
        );
        return value > 0 ? value : DEFAULT_RADIUS;
    }

    async _bootstrapMap() {
        try {
            await ensureLeaflet();
            if (this._destroyed) {
                return;
            }
            this._setupLeafletIcons();
            this._observeResize();
            this._observeVisibility();
            this._scheduleInit();
        } catch (error) {
            console.error("CEMS geofence map:", error);
            this.state.loadError = _t(
                "Map library failed to load. Upgrade the module and hard-refresh the browser."
            );
            const el = this.mapRef.el;
            if (el) {
                el.textContent = this.state.loadError;
                el.classList.add("o_cems_geofence_map_error");
            }
        }
    }

    _scheduleInit() {
        if (this._destroyed) {
            return;
        }
        if (isElementReady(this.mapRef.el)) {
            this._ensureMap();
            return;
        }
        // Poll until notebook tab / container has a real size.
        if (this._pollTimer) {
            return;
        }
        let tries = 0;
        this._pollTimer = setInterval(() => {
            tries += 1;
            if (this._destroyed) {
                this._clearPoll();
                return;
            }
            if (isElementReady(this.mapRef.el)) {
                this._clearPoll();
                this._ensureMap();
                return;
            }
            if (tries > 100) {
                // Last resort: force height and init anyway.
                this._clearPoll();
                const el = this.mapRef.el;
                if (el) {
                    el.style.minHeight = "360px";
                    el.style.height = "360px";
                    el.style.width = "100%";
                }
                this._ensureMap();
            }
        }, 100);
    }

    _clearPoll() {
        if (this._pollTimer) {
            clearInterval(this._pollTimer);
            this._pollTimer = null;
        }
    }

    _setupLeafletIcons() {
        const L = window.L;
        if (!L?.Icon?.Default) {
            return;
        }
        delete L.Icon.Default.prototype._getIconUrl;
        L.Icon.Default.mergeOptions({
            iconUrl: `${ICON_PATH}/marker-icon.png`,
            iconRetinaUrl: `${ICON_PATH}/marker-icon-2x.png`,
            shadowUrl: `${ICON_PATH}/marker-shadow.png`,
        });
    }

    _ensureMap() {
        if (this._destroyed) {
            return;
        }
        if (!this.map) {
            this._setupMap();
        }
        this._invalidateSoon();
    }

    _setupMap() {
        const L = window.L;
        const el = this.mapRef.el;
        if (!L || !el || this.map) {
            return;
        }
        el.classList.remove("o_cems_geofence_map_error");
        el.replaceChildren();
        el.style.minHeight = "360px";
        el.style.height = "360px";
        el.style.width = "100%";

        this.map = L.map(el, {
            zoomControl: true,
            attributionControl: true,
        });

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        }).addTo(this.map);

        this.marker = L.marker([this.centerLat, this.centerLng], {
            draggable: !this.props.readonly,
        }).addTo(this.map);

        this.circle = L.circle([this.centerLat, this.centerLng], {
            radius: this.radius,
            color: "#0d9488",
            fillColor: "#14b8a6",
            fillOpacity: 0.18,
            weight: 2,
        }).addTo(this.map);

        if (!this.props.readonly) {
            this.map.on("click", (ev) => {
                this._commitCenter(ev.latlng.lat, ev.latlng.lng);
            });
            this.marker.on("dragend", () => {
                const latlng = this.marker.getLatLng();
                this._commitCenter(latlng.lat, latlng.lng);
            });
        }

        this.map.setView([this.centerLat, this.centerLng], DEFAULT_ZOOM);
        this._fitCircle();
    }

    _destroyMapOnly() {
        if (this.map) {
            this.map.off();
            this.map.remove();
        }
        this.map = null;
        this.marker = null;
        this.circle = null;
    }

    _observeResize() {
        const el = this.mapRef.el;
        if (!el || typeof ResizeObserver === "undefined") {
            return;
        }
        this.resizeObserver = new ResizeObserver((entries) => {
            const entry = entries[0];
            const box = entry?.contentRect;
            if (box && box.width >= MIN_SIZE && box.height >= MIN_SIZE) {
                if (!this.map) {
                    this._ensureMap();
                } else {
                    this._invalidate();
                }
            }
        });
        this.resizeObserver.observe(el);
    }

    _observeVisibility() {
        const el = this.mapRef.el;
        if (!el) {
            return;
        }

        if (typeof IntersectionObserver !== "undefined") {
            this.intersectionObserver = new IntersectionObserver(
                (entries) => {
                    if (entries.some((entry) => entry.isIntersecting && entry.intersectionRatio > 0)) {
                        this._scheduleInit();
                        this._invalidateSoon();
                    }
                },
                { threshold: [0, 0.01, 0.1] }
            );
            this.intersectionObserver.observe(el);
        }

        this._tabPane = el.closest(".tab-pane");
        if (this._tabPane) {
            this._tabListener = () => {
                // Recreate if previous init happened at size 0.
                if (this.map && (el.clientWidth < MIN_SIZE || el.clientHeight < MIN_SIZE)) {
                    this._destroyMapOnly();
                }
                this._scheduleInit();
                this._invalidateSoon();
            };
            this._tabPane.addEventListener("shown.bs.tab", this._tabListener);
            const tabId = this._tabPane.getAttribute("id");
            if (tabId) {
                const trigger = document.querySelector(
                    `[data-bs-target="#${CSS.escape(tabId)}"], a[href="#${CSS.escape(tabId)}"]`
                );
                // Also listen on nav-item clicks used by Odoo notebook
                const navLink =
                    trigger ||
                    document.querySelector(`.nav-link[name="cems_geofence"], a[name="cems_geofence"]`);
                navLink?.addEventListener("click", this._tabListener);
                this._tabTrigger = navLink;
            }
            // Odoo may toggle classes without Bootstrap events.
            this._mutationObserver = new MutationObserver(() => {
                if (isElementReady(el)) {
                    this._scheduleInit();
                    this._invalidateSoon();
                }
            });
            this._mutationObserver.observe(this._tabPane, {
                attributes: true,
                attributeFilter: ["class", "style"],
            });
        }
    }

    _invalidateSoon() {
        requestAnimationFrame(() => {
            this._invalidate();
            setTimeout(() => this._invalidate(), 50);
            setTimeout(() => this._invalidate(), 250);
        });
    }

    _invalidate() {
        if (!this.map) {
            return;
        }
        const el = this.mapRef.el;
        if (el) {
            el.style.minHeight = "360px";
            el.style.height = "360px";
        }
        this.map.invalidateSize({ animate: false });
        this._fitCircle();
        // Force tile redraw
        this.map.eachLayer((layer) => {
            if (layer.redraw) {
                layer.redraw();
            }
        });
    }

    _syncFromRecord() {
        if (!this.map || !this.marker || !this.circle) {
            return;
        }
        const lat = this.centerLat;
        const lng = this.centerLng;
        const radius = this.radius;
        this.marker.setLatLng([lat, lng]);
        if (this.marker.dragging) {
            if (this.props.readonly) {
                this.marker.dragging.disable();
            } else {
                this.marker.dragging.enable();
            }
        }
        this.circle.setLatLng([lat, lng]);
        this.circle.setRadius(radius);
        this._fitCircle();
    }

    _fitCircle() {
        if (!this.map || !this.circle) {
            return;
        }
        try {
            this.map.fitBounds(this.circle.getBounds(), { padding: [28, 28], maxZoom: 18 });
        } catch {
            this.map.setView([this.centerLat, this.centerLng], DEFAULT_ZOOM);
        }
    }

    async _commitCenter(lat, lng) {
        if (this.props.readonly) {
            return;
        }
        const nextLat = Number(lat.toFixed(7));
        const nextLng = Number(lng.toFixed(7));
        this._updatingFromMap = true;
        this.marker.setLatLng([nextLat, nextLng]);
        this.circle.setLatLng([nextLat, nextLng]);
        await this.props.record.update({
            [this.props.latField]: nextLat,
            [this.props.lngField]: nextLng,
        });
        this._updatingFromMap = false;
        this._fitCircle();
    }

    async onRadiusInput(ev) {
        const value = toFiniteNumber(ev.target.value, this.radius);
        this.state.radiusInput = value;
        this.circle?.setRadius(value > 0 ? value : DEFAULT_RADIUS);
    }

    async onRadiusChange(ev) {
        if (this.props.readonly) {
            return;
        }
        let value = toFiniteNumber(ev.target.value, DEFAULT_RADIUS);
        if (value < 1) {
            value = 1;
        }
        this.state.radiusInput = value;
        this._updatingFromMap = true;
        this.circle?.setRadius(value);
        await this.props.record.update({
            [this.props.radiusField]: value,
        });
        this._updatingFromMap = false;
        this._fitCircle();
    }

    async onUseMyLocation() {
        if (this.props.readonly || !navigator.geolocation) {
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                this._commitCenter(pos.coords.latitude, pos.coords.longitude);
            },
            () => {},
            { enableHighAccuracy: true, timeout: 10000 }
        );
    }

    _teardown() {
        this._clearPoll();
        this.resizeObserver?.disconnect();
        this.resizeObserver = null;
        this.intersectionObserver?.disconnect();
        this.intersectionObserver = null;
        this._mutationObserver?.disconnect();
        this._mutationObserver = null;
        if (this._tabPane && this._tabListener) {
            this._tabPane.removeEventListener("shown.bs.tab", this._tabListener);
        }
        if (this._tabTrigger && this._tabListener) {
            this._tabTrigger.removeEventListener("click", this._tabListener);
        }
        this._tabPane = null;
        this._tabTrigger = null;
        this._tabListener = null;
        this._destroyMapOnly();
    }
}

export const cemsGeofenceMapField = {
    component: CemsGeofenceMapField,
    displayName: _t("CEMS Geofence Map"),
    supportedTypes: ["char", "float"],
    extractProps: ({ options }) => ({
        latField: options.lat_field || "geofence_latitude",
        lngField: options.lng_field || "geofence_longitude",
        radiusField: options.radius_field || "geofence_radius",
    }),
};

registry.category("fields").add("cems_geofence_map", cemsGeofenceMapField);
