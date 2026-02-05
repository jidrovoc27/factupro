// Trae información del cliente y detecta características del dispositivo
async function getClientInfo() {
    // Obtener IP (tu función existente)
    const clientIP = await obtenerIPPublica(); // o tu método actual

    // Detectar información básica del navegador
    const browser = detectBrowser();
    const os = detectOS();
    const deviceType = detectDeviceType();

    // NUEVAS VALIDACIONES ANTI-MÓVIL
    const deviceData = {
        // Datos básicos existentes
        browser: browser,
        os: os,
        deviceType: deviceType,
        clientIP: clientIP,
        screenSize: `${screen.width}x${screen.height}`,

        // NUEVOS DATOS PARA DETECTAR MÓVILES
        screen_width: screen.width,
        screen_height: screen.height,
        window_width: window.innerWidth,
        window_height: window.innerHeight,
        pixel_ratio: window.devicePixelRatio || 1,

        // Capacidades del dispositivo
        touch_support: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
        max_touch_points: navigator.maxTouchPoints || 0,
        device_memory: navigator.deviceMemory || 0,
        hardware_concurrency: navigator.hardwareConcurrency || 0,

        // APIs típicas de móviles
        battery_api: 'getBattery' in navigator,
        vibration_api: 'vibrate' in navigator,
        device_motion: 'DeviceMotionEvent' in window,
        device_orientation: 'DeviceOrientationEvent' in window,

        // Información de conexión
        connection_type: navigator.connection ? navigator.connection.effectiveType : 'unknown',
        connection_downlink: navigator.connection ? navigator.connection.downlink : 0,

        // Orientación
        orientation_angle: screen.orientation ? screen.orientation.angle : (window.orientation || 0),
        orientation_type: screen.orientation ? screen.orientation.type : 'unknown',

        // Información temporal
        timezone_offset: new Date().getTimezoneOffset(),
        timestamp: Date.now(),

        // User Agent completo
        user_agent_full: navigator.userAgent,

        // Validaciones específicas
        is_likely_mobile: detectMobileFeatures(),
        viewport_mobile: window.innerWidth <= 768,
        high_pixel_ratio: (window.devicePixelRatio || 1) > 1.5,

        // Información adicional sospechosa
        plugins_count: navigator.plugins ? navigator.plugins.length : 0,
        languages: navigator.languages ? navigator.languages.join(',') : navigator.language,

        // Detección de cambios de orientación previos
        orientation_changes: getOrientationHistory()
    };

    return deviceData;
}

// Variables globales para rastrear orientación
let orientationHistory = [];
let lastOrientation = screen.orientation ? screen.orientation.type : 'unknown';

// Función para detectar características móviles
function detectMobileFeatures() {
    let mobileScore = 0;
    const maxScore = 15; // Aumentamos el máximo

    console.log('=== CALCULANDO MOBILE SCORE ===');

    // APIs exclusivas de móviles (peso alto)
    if ('getBattery' in navigator) {
        mobileScore += 3;
        console.log('+3 Battery API');
    }
    if ('vibrate' in navigator) {
        mobileScore += 3;
        console.log('+3 Vibration API');
    }

    // Soporte táctil (pero menos peso)
    if ('ontouchstart' in window) {
        mobileScore += 1;
        console.log('+1 Touch start');
    }
    if (navigator.maxTouchPoints > 0) {
        mobileScore += 1;
        console.log('+1 Touch points:', navigator.maxTouchPoints);
    }
    if (navigator.maxTouchPoints >= 10) { // Pantallas muy avanzadas
        mobileScore += 2;
        console.log('+2 Muchos touch points');
    }

    // APIs de sensores
    if ('DeviceMotionEvent' in window) {
        mobileScore += 1;
        console.log('+1 Device Motion');
    }
    if ('DeviceOrientationEvent' in window) {
        mobileScore += 1;
        console.log('+1 Device Orientation');
    }

    // Características de pantalla
    const pixelRatio = window.devicePixelRatio || 1;
    if (pixelRatio >= 3 && screen.width <= 414) {
        mobileScore += 3;
        console.log('+3 Pixel ratio alto en pantalla pequeña');
    } else if (pixelRatio > 2 && screen.width <= 768) {
        mobileScore += 1;
        console.log('+1 Pixel ratio medio');
    }

    // Resolución muy pequeña
    if (screen.width <= 414) {
        mobileScore += 2;
        console.log('+2 Pantalla muy pequeña');
    } else if (screen.width <= 768) {
        mobileScore += 1;
        console.log('+1 Pantalla pequeña');
    }

    // Memoria muy limitada (solo muy poco RAM)
    if (navigator.deviceMemory && navigator.deviceMemory <= 2) {
        mobileScore += 2;
        console.log('+2 Muy poca memoria:', navigator.deviceMemory + 'GB');
    }

    console.log('MOBILE SCORE FINAL:', mobileScore + '/' + maxScore);

    // Aumentamos el umbral para ser menos agresivo
    return mobileScore >= 8; // Era 5, ahora 8
}

// Función para obtener historial de orientaciones
function getOrientationHistory() {
    return orientationHistory;
}

// Escuchar cambios de orientación
function initOrientationTracking() {
    // Registrar orientación inicial
    orientationHistory.push({
        orientation: lastOrientation,
        timestamp: Date.now()
    });

    // Escuchar cambios
    if (screen.orientation) {
        screen.orientation.addEventListener('change', () => {
            const newOrientation = screen.orientation.type;
            if (newOrientation !== lastOrientation) {
                orientationHistory.push({
                    orientation: newOrientation,
                    timestamp: Date.now()
                });
                lastOrientation = newOrientation;

                // Mantener solo los últimos 10 cambios
                if (orientationHistory.length > 10) {
                    orientationHistory.shift();
                }
            }
        });
    } else if (window.orientation !== undefined) {
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                const newOrientation = Math.abs(window.orientation) === 90 ? 'landscape' : 'portrait';
                if (newOrientation !== lastOrientation) {
                    orientationHistory.push({
                        orientation: newOrientation,
                        timestamp: Date.now()
                    });
                    lastOrientation = newOrientation;
                }
            }, 100);
        });
    }
}

// Validación antes de permitir marcación
function validateDeviceBeforeMarking() {
    const deviceData = {
        screen_width: screen.width,
        screen_height: screen.height,
        touch_support: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
        pixel_ratio: window.devicePixelRatio || 1,
        is_likely_mobile: detectMobileFeatures(),
        orientation_changes: orientationHistory.length > 1,
        viewport_mobile: window.innerWidth <= 768,
        max_touch_points: navigator.maxTouchPoints || 0
    };

    console.log('=== DEBUG VALIDACIÓN DISPOSITIVO ===');
    console.log('Screen:', deviceData.screen_width + 'x' + deviceData.screen_height);
    console.log('Window:', window.innerWidth + 'x' + window.innerHeight);
    console.log('Touch support:', deviceData.touch_support);
    console.log('Touch points:', deviceData.max_touch_points);
    console.log('Pixel ratio:', deviceData.pixel_ratio);
    console.log('Is likely mobile:', deviceData.is_likely_mobile);
    console.log('Viewport mobile:', deviceData.viewport_mobile);
    console.log('Orientation changes:', deviceData.orientation_changes);

    // VALIDACIÓN 1: Pantalla muy pequeña + muchos puntos táctiles = móvil
    if (deviceData.screen_width <= 414 && deviceData.max_touch_points >= 5) {
        console.log('❌ BLOQUEADO: Pantalla móvil + multitáctil avanzado');
        throw new Error('Dispositivo móvil detectado por resolución y capacidades táctiles');
    }

    // VALIDACIÓN 2: Cambios de orientación en pantalla pequeña
    if (deviceData.orientation_changes && deviceData.screen_width <= 768) {
        console.log('❌ BLOQUEADO: Cambios de orientación en pantalla pequeña');
        throw new Error('Se detectó cambio de orientación en dispositivo móvil');
    }

    // VALIDACIÓN 3: Pixel ratio muy alto en pantalla muy pequeña (móviles premium)
    if (deviceData.pixel_ratio >= 3 && deviceData.screen_width <= 414) {
        console.log('❌ BLOQUEADO: Pixel ratio alto + pantalla muy pequeña');
        throw new Error('Resolución típica de móvil premium detectada');
    }

    // VALIDACIÓN 4: Viewport móvil + soporte táctil + orientación portrait
    const isPortrait = screen.height > screen.width;
    if (deviceData.viewport_mobile && deviceData.touch_support && isPortrait && deviceData.screen_width <= 768) {
        console.log('❌ BLOQUEADO: Viewport móvil + táctil + portrait');
        throw new Error('Configuración típica de móvil detectada');
    }

    console.log('✅ DISPOSITIVO PERMITIDO');
    return true;
}

// Traer IP pública del cliente con múltiples servicios y WebRTC
async function obtenerIPPublica() {
    const serviciosIP = [
        'https://api.ipify.org?format=json',
        'https://ipapi.co/json/',
        'https://jsonip.com/',
        'https://api.myip.com',
        'https://ipinfo.io/json',
        'https://api64.ipify.org?format=json'
    ];

    for (const servicio of serviciosIP) {
        try {
            const response = await fetch(servicio, {
                method: 'GET',
                timeout: 5000 // 5 segundos de timeout
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Diferentes servicios devuelven la IP en diferentes campos
            let ip = null;
            if (data.ip) {
                ip = data.ip;
            } else if (data.query) {
                ip = data.query; // ipapi.co
            } else if (data.IP) {
                ip = data.IP; // api.myip.com
            }

            // Validar que la IP sea válida
            if (ip && esIPValida(ip)) {
                console.log(`IP obtenida de ${servicio}: ${ip}`);
                return ip;
            }

        } catch (error) {
            console.warn(`Error con servicio ${servicio}:`, error.message);
            continue; // Probar el siguiente servicio
        }
    }

    // Si todos los servicios fallan, intentar método alternativo
    try {
        return await obtenerIPAlternativa();
    } catch (error) {
        console.error('No se pudo obtener la IP del cliente:', error);
        return 'IP_NO_DISPONIBLE';
    }
}

// Función para validar formato de IP
function esIPValida(ip) {
    const ipv4Regex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    const ipv6Regex = /^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/;

    return ipv4Regex.test(ip) || ipv6Regex.test(ip);
}

// Método alternativo usando WebRTC (puede revelar IP local también)
async function obtenerIPAlternativa() {
    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
            reject(new Error('Timeout obteniendo IP alternativa'));
        }, 10000);

        // Crear conexión WebRTC para obtener IP
        const rtc = new RTCPeerConnection({
            iceServers: [
                {urls: 'stun:stun.l.google.com:19302'},
                {urls: 'stun:stun1.l.google.com:19302'}
            ]
        });

        rtc.createDataChannel('', {ordered: true});

        rtc.onicecandidate = (event) => {
            if (event.candidate) {
                const candidate = event.candidate.candidate;
                const ipMatch = candidate.match(/([0-9]{1,3}(\.[0-9]{1,3}){3})/);

                if (ipMatch && ipMatch[1]) {
                    const ip = ipMatch[1];
                    // Filtrar IPs locales/privadas
                    if (!esIPLocal(ip)) {
                        clearTimeout(timeout);
                        rtc.close();
                        resolve(ip);
                    }
                }
            }
        };

        rtc.createOffer()
            .then(offer => rtc.setLocalDescription(offer))
            .catch(reject);
    });
}

// Función para detectar IPs locales/privadas
function esIPLocal(ip) {
    const partesIP = ip.split('.').map(Number);

    // Rangos de IPs privadas
    return (
        partesIP[0] === 10 || // 10.0.0.0/8
        (partesIP[0] === 172 && partesIP[1] >= 16 && partesIP[1] <= 31) || // 172.16.0.0/12
        (partesIP[0] === 192 && partesIP[1] === 168) || // 192.168.0.0/16
        partesIP[0] === 127 || // 127.0.0.0/8 (localhost)
        partesIP[0] === 0 // 0.0.0.0/8
    );
}

// Detectar navegador - Simple y preciso
function detectBrowser() {
    const ua = navigator.userAgent;

    if (ua.includes('Edg/')) return 'Edge';
    if (ua.includes('Chrome/')) return 'Chrome';
    if (ua.includes('Firefox/')) return 'Firefox';
    if (ua.includes('Safari/') && !ua.includes('Chrome')) return 'Safari';
    if (ua.includes('Opera/') || ua.includes('OPR/')) return 'Opera';

    return 'Unknown';
}

// Detectar sistema operativo - Simple y preciso
function detectOS() {
    const ua = navigator.userAgent;

    if (ua.includes('Windows')) return 'Windows';
    if (ua.includes('Mac OS')) return 'MacOS';
    if (ua.includes('Linux')) return 'Linux';
    if (ua.includes('Android')) return 'Android';
    if (ua.includes('iPhone') || ua.includes('iPad')) return 'iOS';

    return 'Unknown';
}

// Detectar tipo de dispositivo - Simple y preciso
function detectDeviceType() {
    const ua = navigator.userAgent;

    if (/iPhone|iPod|Android.*Mobile/i.test(ua)) return 'Mobile';
    if (/iPad|Android(?!.*Mobile)/i.test(ua)) return 'Tablet';

    return 'Desktop';
}