/**
 * Client-Side Face Processing using face-api.js
 * Offloads heavy face detection/encoding from Raspberry Pi to client browser
 */

const FaceProcessor = {
    modelsLoaded: false,
    modelPath: 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.12/model/',
    
    /**
     * Load face-api.js models on initialization
     */
    async loadModels() {
        if (this.modelsLoaded) return true;
        
        try {
            console.log('Loading face detection models...');
            
            // Load required models
            await faceapi.nets.tinyFaceDetector.loadFromUri(this.modelPath);
            await faceapi.nets.faceLandmark68Net.loadFromUri(this.modelPath);
            await faceapi.nets.faceRecognitionNet.loadFromUri(this.modelPath);
            
            this.modelsLoaded = true;
            console.log('✅ Face models loaded successfully');
            return true;
        } catch (error) {
            console.error('❌ Failed to load face models:', error);
            return false;
        }
    },
    
    /**
     * Detect face and extract 128D descriptor from video element
     * @param {HTMLVideoElement} videoElement - Video element with camera feed
     * @returns {Object|null} - {descriptor, landmarks, angle, box} or null if no face
     */
    async detectFace(videoElement) {
        if (!this.modelsLoaded) {
            await this.loadModels();
        }
        
        try {
            const detection = await faceapi
                .detectSingleFace(videoElement, new faceapi.TinyFaceDetectorOptions({
                    inputSize: 320,
                    scoreThreshold: 0.5
                }))
                .withFaceLandmarks()
                .withFaceDescriptor();
            
            if (!detection) {
                return null;
            }
            
            // Calculate face angle from landmarks
            const angle = this.calculateFaceAngle(detection.landmarks);
            
            return {
                descriptor: Array.from(detection.descriptor), // Convert Float32Array to regular array
                landmarks: detection.landmarks,
                angle: angle,
                box: detection.detection.box,
                score: detection.detection.score
            };
        } catch (error) {
            console.error('Face detection error:', error);
            return null;
        }
    },
    
    /**
     * Calculate face angle (yaw, pitch, roll) from landmarks
     * @param {Object} landmarks - Face landmarks from face-api.js
     * @returns {Object} - {yaw, pitch, roll}
     */
    calculateFaceAngle(landmarks) {
        const nose = landmarks.getNose();
        const leftEye = landmarks.getLeftEye();
        const rightEye = landmarks.getRightEye();
        const mouth = landmarks.getMouth();
        
        // Get key points
        const noseTip = nose[3];
        const leftEyeCenter = this.getCenter(leftEye);
        const rightEyeCenter = this.getCenter(rightEye);
        const mouthCenter = this.getCenter(mouth);
        
        // Calculate yaw (left-right rotation)
        const eyeDistance = rightEyeCenter.x - leftEyeCenter.x;
        const noseToLeftEye = noseTip.x - leftEyeCenter.x;
        const noseToRightEye = rightEyeCenter.x - noseTip.x;
        const yaw = ((noseToRightEye - noseToLeftEye) / eyeDistance) * 30; // Scale to degrees
        
        // Calculate pitch (up-down rotation)
        const eyeMidpoint = (leftEyeCenter.y + rightEyeCenter.y) / 2;
        const faceHeight = mouthCenter.y - eyeMidpoint;
        const noseTilt = noseTip.y - eyeMidpoint;
        const pitch = (noseTilt / faceHeight) * 30;
        
        // Calculate roll (tilt)
        const eyeDeltaY = rightEyeCenter.y - leftEyeCenter.y;
        const eyeDeltaX = rightEyeCenter.x - leftEyeCenter.x;
        const roll = Math.atan2(eyeDeltaY, eyeDeltaX) * (180 / Math.PI);
        
        return {
            yaw: Math.round(yaw * 10) / 10,
            pitch: Math.round(pitch * 10) / 10,
            roll: Math.round(roll * 10) / 10
        };
    },
    
    /**
     * Get center point of landmark array
     */
    getCenter(points) {
        const x = points.reduce((sum, p) => sum + p.x, 0) / points.length;
        const y = points.reduce((sum, p) => sum + p.y, 0) / points.length;
        return { x, y };
    },
    
    /**
     * Check if angle is significantly different from previous angles
     * @param {Object} newAngle - {yaw, pitch, roll}
     * @param {Array} capturedAngles - Array of previously captured angles
     * @param {Number} threshold - Minimum difference in degrees
     * @returns {Boolean}
     */
    isAngleDifferent(newAngle, capturedAngles, threshold = 7) {
        if (capturedAngles.length === 0) return true;
        
        for (const angle of capturedAngles) {
            const yawDiff = Math.abs(newAngle.yaw - angle.yaw);
            const pitchDiff = Math.abs(newAngle.pitch - angle.pitch);
            const rollDiff = Math.abs(newAngle.roll - angle.roll);
            
            // Euclidean distance in angle space
            const distance = Math.sqrt(yawDiff ** 2 + pitchDiff ** 2 + rollDiff ** 2);
            
            if (distance < threshold) {
                return false; // Too similar to existing angle
            }
        }
        
        return true; // Sufficiently different
    },
    
    /**
     * Log face data for debugging
     */
    logFaceData(faceData) {
        console.log('=== FACE DATA CAPTURED (CLIENT-SIDE) ===');
        console.log('Descriptor length:', faceData.descriptor.length);
        console.log('Descriptor type:', typeof faceData.descriptor[0]);
        console.log('Sample values:', faceData.descriptor.slice(0, 5).map(v => v.toFixed(4)));
        console.log('Angle:', faceData.angle);
        console.log('Detection score:', faceData.score.toFixed(3));
        console.log('Bounding box:', faceData.box);
        console.log('Descriptor min:', Math.min(...faceData.descriptor).toFixed(4));
        console.log('Descriptor max:', Math.max(...faceData.descriptor).toFixed(4));
        console.log('Descriptor mean:', (faceData.descriptor.reduce((a, b) => a + b) / faceData.descriptor.length).toFixed(4));
    },
    
    /**
     * Compare two face descriptors (cosine similarity)
     * @returns {Number} - Similarity score 0-1 (1 = identical)
     */
    compareDescriptors(desc1, desc2) {
        const distance = faceapi.euclideanDistance(desc1, desc2);
        return 1 - distance; // Convert distance to similarity
    },
    
    /**
     * Draw face axis visualization on canvas
     * @param {CanvasRenderingContext2D} ctx - Canvas context
     * @param {Object} landmarks - Face landmarks
     * @param {Object} angle - {yaw, pitch, roll}
     * @param {Object} box - Bounding box {x, y, width, height}
     */
    drawFaceAxis(ctx, landmarks, angle, box) {
        const nose = landmarks.getNose();
        const noseTip = nose[3];
        const centerX = noseTip.x;
        const centerY = noseTip.y;
        const axisLength = 80;
        
        // Calculate axis endpoints based on angles
        const yawRad = (angle.yaw * Math.PI) / 180;
        const pitchRad = (angle.pitch * Math.PI) / 180;
        const rollRad = (angle.roll * Math.PI) / 180;
        
        // X-axis (Yaw - Red)
        const xEndX = centerX + axisLength * Math.cos(yawRad);
        const xEndY = centerY + axisLength * Math.sin(yawRad);
        
        ctx.strokeStyle = '#FF0000';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(xEndX, xEndY);
        ctx.stroke();
        
        // Y-axis (Pitch - Green)
        const yEndX = centerX;
        const yEndY = centerY - axisLength * Math.cos(pitchRad);
        
        ctx.strokeStyle = '#00FF00';
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(yEndX, yEndY);
        ctx.stroke();
        
        // Z-axis (Roll - Blue)
        const zEndX = centerX + axisLength * Math.sin(rollRad);
        const zEndY = centerY + axisLength * Math.cos(rollRad);
        
        ctx.strokeStyle = '#0000FF';
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(zEndX, zEndY);
        ctx.stroke();
        
        // Draw center point
        ctx.fillStyle = '#FFFF00';
        ctx.beginPath();
        ctx.arc(centerX, centerY, 5, 0, 2 * Math.PI);
        ctx.fill();
        
        // Draw angle values
        ctx.font = 'bold 16px Arial';
        ctx.fillStyle = '#FFFFFF';
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 3;
        
        const textX = box.x + box.width + 10;
        const textY = box.y + 20;
        
        const lines = [
            `Yaw: ${angle.yaw.toFixed(1)}°`,
            `Pitch: ${angle.pitch.toFixed(1)}°`,
            `Roll: ${angle.roll.toFixed(1)}°`
        ];
        
        lines.forEach((line, i) => {
            const y = textY + (i * 25);
            ctx.strokeText(line, textX, y);
            ctx.fillText(line, textX, y);
        });
    }
};

// Initialize face processor
window.FaceProcessor = FaceProcessor;

// Preload models when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // Small delay to let other resources load first
        setTimeout(() => FaceProcessor.loadModels(), 1000);
    });
} else {
    setTimeout(() => FaceProcessor.loadModels(), 1000);
}
