// detection.js - Sistema de detección facial con prevención de conflictos

// Encapsular todo en un namespace para evitar conflictos
window.FaceDetection = window.FaceDetection || {};

(function() {
    'use strict';

    // Variables locales para evitar conflictos globales
    let detectionSequence = [];
    let detectionCurrentStep = 0;

    // Funciones de cálculo y detección
    function calculateEAR(eye) {
        const A = Math.hypot(eye[1].x - eye[5].x, eye[1].y - eye[5].y);
        const B = Math.hypot(eye[2].x - eye[4].x, eye[2].y - eye[4].y);
        const C = Math.hypot(eye[0].x - eye[3].x, eye[0].y - eye[3].y);
        return (A + B) / (2.0 * C);
    }

    function detectLeftMovement(noseX) {
        const leftThreshold = 0.60;
        return noseX > leftThreshold;
    }

    function detectRightMovement(noseX) {
        return noseX < 0.45;
    }

    function detectSmile(mouthLeftX, mouthRightX) {
        const mouthWidth = Math.abs(mouthRightX - mouthLeftX);
        return mouthWidth > 0.10;
    }

    function detectBlink(leftEAR, rightEAR) {
        leftEAR = calculateEAR(leftEAR);
        rightEAR = calculateEAR(rightEAR);
        return (leftEAR < 0.2 || rightEAR < 0.2);
    }

    function detectSerious(mouthLeftX, mouthRightX) {
        const mouthWidth = Math.abs(mouthRightX - mouthLeftX);
        return mouthWidth < 0.9;
    }

    function detectHeadUp(noseY, chinY) {
        return chinY > noseY + 0.2;
    }

    function detectHeadDown(noseY, chinY) {
        const threshold = 0.18;
        return (chinY - noseY) > threshold;
    }

    function detectMouthOpen(mouthTopY, mouthBottomY) {
        return Math.abs(mouthBottomY - mouthTopY) > 0.03;
    }

    function detectTiltLeft(noseX, chinX) {
        const tiltThreshold = 0.05;
        return (noseX - chinX) > tiltThreshold;
    }

    function detectTiltRight(noseX, chinX) {
        const tiltThreshold = 0.05;
        return (chinX - noseX) > tiltThreshold;
    }

    function captureInitialBrowDistance(landmarks) {
        const browLeftX = landmarks[70].x;
        const browRightX = landmarks[107].x;
        return Math.abs(browRightX - browLeftX);
    }

    function generateSequence() {
        const movements = [
            'smile',
            'blink',
            'tiltLeft',
            'tiltRight',
        ];

        detectionSequence = [];
        for (let i = 0; i < 3; i++) {  // Generar 3 pasos aleatorios
            const randomIndex = Math.floor(Math.random() * movements.length);
            detectionSequence.push(movements[randomIndex]);
        }
        console.log("Secuencia generada:", detectionSequence);
        updateInstructions();
    }

    function updateInstructions() {
        const instructions = {
            'smile': 'Sonríe',
            'blink': 'Parpadea',
            'tiltLeft': 'Inclina la cabeza hacia la izquierda',
            'tiltRight': 'Inclina la cabeza hacia la derecha',
        };

        const instructionElement = document.getElementById('instructions');
        if (instructionElement) {
            if (detectionCurrentStep < detectionSequence.length) {
                instructionElement.innerText = `${instructions[detectionSequence[detectionCurrentStep]]}`;
            } else {
                const resultElement = document.getElementById('result');
                if (resultElement) {
                    resultElement.innerText = 'Prueba de vida completada con éxito';
                }
            }
        }
    }

    function resetSequence() {
        detectionCurrentStep = 0;
        generateSequence();
        updateInstructions();
    }

    // Exponer funciones necesarias al scope global
    window.FaceDetection = {
        // Funciones de detección
        detectSmile: detectSmile,
        detectBlink: detectBlink,
        detectTiltLeft: detectTiltLeft,
        detectTiltRight: detectTiltRight,
        detectLeftMovement: detectLeftMovement,
        detectRightMovement: detectRightMovement,
        detectSerious: detectSerious,
        detectHeadUp: detectHeadUp,
        detectHeadDown: detectHeadDown,
        detectMouthOpen: detectMouthOpen,
        captureInitialBrowDistance: captureInitialBrowDistance,

        // Funciones de secuencia
        generateSequence: generateSequence,
        updateInstructions: updateInstructions,
        resetSequence: resetSequence,

        // Getters para variables
        getCurrentStep: function() { return detectionCurrentStep; },
        getSequence: function() { return detectionSequence; },
        getSequenceLength: function() { return detectionSequence.length; },

        // Setters
        incrementStep: function() { detectionCurrentStep++; },
        setCurrentStep: function(step) { detectionCurrentStep = step; }
    };

    // Para compatibilidad con código existente, exponer variables globales
    // solo si no existen ya
    if (typeof window.sequence === 'undefined') {
        Object.defineProperty(window, 'sequence', {
            get: function() { return detectionSequence; },
            set: function(value) { detectionSequence = value; }
        });
    }

    if (typeof window.currentStep === 'undefined') {
        Object.defineProperty(window, 'currentStep', {
            get: function() { return detectionCurrentStep; },
            set: function(value) { detectionCurrentStep = value; }
        });
    }

    // Exponer funciones individuales para compatibilidad
    window.detectSmile = detectSmile;
    window.detectBlink = detectBlink;
    window.detectTiltLeft = detectTiltLeft;
    window.detectTiltRight = detectTiltRight;
    window.captureInitialBrowDistance = captureInitialBrowDistance;
    window.resetSequence = resetSequence;
    window.updateInstructions = updateInstructions;

})();

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    if (window.FaceDetection) {
        window.FaceDetection.resetSequence();
    }
});