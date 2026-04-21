// Face API Logic for Edge Cases

const MODEL_URL = 'https://vladmandic.github.io/face-api/model/';

let isModelsLoaded = false;
let hasSmiled = false;

// Helper to calculate Blur (Variance of Laplacian)
function calculateBlur(videoElem, blurCanvasElem) {
    const ctx = blurCanvasElem.getContext('2d', { willReadFrequently: true });
    blurCanvasElem.width = videoElem.videoWidth || 640;
    blurCanvasElem.height = videoElem.videoHeight || 480;
    ctx.drawImage(videoElem, 0, 0, blurCanvasElem.width, blurCanvasElem.height);
    
    const imageData = ctx.getImageData(0, 0, blurCanvasElem.width, blurCanvasElem.height);
    const pixels = imageData.data;
    const width = blurCanvasElem.width;
    const height = blurCanvasElem.height;
    
    const gray = new Uint8Array(width * height);
    for (let i = 0; i < pixels.length; i += 4) {
        gray[i / 4] = 0.299 * pixels[i] + 0.587 * pixels[i+1] + 0.114 * pixels[i+2];
    }
    
    let sum = 0, count = 0;
    let laplacian = new Int16Array(width * height);
    
    for (let y = 1; y < height - 1; y++) {
        for (let x = 1; x < width - 1; x++) {
            const idx = y * width + x;
            const val = gray[idx - width] + gray[idx - 1] - 4 * gray[idx] + gray[idx + 1] + gray[idx + width];
            laplacian[idx] = Math.abs(val);
            sum += laplacian[idx];
            count++;
        }
    }
    
    const mean = sum / count;
    let variance = 0;
    for (let i = 0; i < laplacian.length; i++) {
        if(laplacian[i] !== 0) variance += Math.pow(laplacian[i] - mean, 2);
    }
    return variance / count;
}


async function loadModels() {
    await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
    await faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL); 
    await faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL); // Load landmarks for 68 points
    isModelsLoaded = true;
    console.log("Models loaded");
}

// We need an off-screen canvas for blur check so we don't mess up the visible drawing canvas
const blurCanvas = document.createElement('canvas');

async function startFaceLogic(video, canvas, msgElement, submitBtn) {
    if (!isModelsLoaded) await loadModels();

    setInterval(async () => {
        if (video.paused || video.ended || video.videoWidth === 0) return;

        // Detect face, expressions, and landmarks
        const detections = await faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions())
                                       .withFaceLandmarks()
                                       .withFaceExpressions();

        // Draw Landmarks
        const displaySize = { width: video.videoWidth, height: video.videoHeight };
        faceapi.matchDimensions(canvas, displaySize);
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (detections.length > 0) {
            const resizedDetections = faceapi.resizeResults(detections, displaySize);
            // Draw points with custom styling (neon green)
            faceapi.draw.drawFaceLandmarks(canvas, resizedDetections, { drawLines: true, color: '#10b981' });
        }

        let canCapture = false;

        if (detections.length === 0) {
            msgElement.innerText = "No face detected. Please look at the camera.";
            msgElement.style.display = "block";
            msgElement.style.background = "rgba(239, 68, 68, 0.8)"; // Red
            hasSmiled = false;
        } else if (detections.length > 1) {
            msgElement.innerText = "Multiple faces detected! Only one person allowed.";
            msgElement.style.display = "block";
            msgElement.style.background = "rgba(239, 68, 68, 0.8)"; // Red
            hasSmiled = false;
        } else {
            const variance = calculateBlur(video, blurCanvas);
            
            if (variance < 15) { 
                msgElement.innerText = "Image is too blurry. Clean lens or fix lighting.";
                msgElement.style.display = "block";
                msgElement.style.background = "rgba(245, 158, 11, 0.8)"; // Orange
            } else {
                const expressions = detections[0].expressions;
                
                if (expressions.happy > 0.5) {
                    hasSmiled = true;
                }

                if (!hasSmiled) {
                    msgElement.innerText = "Liveness Check: Please smile to unlock capture.";
                    msgElement.style.display = "block";
                    msgElement.style.background = "rgba(59, 130, 246, 0.8)"; // Blue
                } else {
                    msgElement.innerText = "Ready to capture. You may click the button.";
                    msgElement.style.display = "block";
                    msgElement.style.background = "rgba(16, 185, 129, 0.8)"; // Green
                    canCapture = true;
                }
            }
        }

        if (submitBtn) {
            submitBtn.disabled = !canCapture;
        }

    }, 200); 
}
