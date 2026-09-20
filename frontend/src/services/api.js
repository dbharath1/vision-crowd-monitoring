import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
});


// ============================================
// VIDEO
// ============================================

export const uploadVideo = async (file) => {
    const formData = new FormData();

    formData.append("file", file);

    const response = await api.post(
        "/api/video/upload",
        formData,
        {
            headers: {
                "Content-Type":
                    "multipart/form-data",
            },
        }
    );

    return response.data;
};


// ============================================
// ANALYSIS
// ============================================

export const startAnalysis = async (
    sessionId
) => {
    const response = await api.post(
        `/api/analysis/start/${sessionId}`
    );

    return response.data;
};


export const getAnalysisStatus = async (
    sessionId
) => {
    const response = await api.get(
        `/api/analysis/${sessionId}/status`
    );

    return response.data;
};


export const getAnalysisSummary = async (
    sessionId
) => {
    const response = await api.get(
        `/api/analysis/${sessionId}/summary`
    );

    return response.data;
};


export const getFrames = async (
    sessionId,
    skip = 0,
    limit = 300
) => {
    const response = await api.get(
        `/api/analysis/${sessionId}/frames`,
        {
            params: {
                skip,
                limit,
            },
        }
    );

    return response.data;
};


export const getTracks = async (
    sessionId,
    frameId = null
) => {
    const params = {};

    if (frameId !== null) {
        params.frame_id = frameId;
    }

    const response = await api.get(
        `/api/analysis/${sessionId}/tracks`,
        {
            params,
        }
    );

    return response.data;
};


export const getGroups = async (
    sessionId,
    frameId = null
) => {
    const params = {};

    if (frameId !== null) {
        params.frame_id = frameId;
    }

    const response = await api.get(
        `/api/analysis/${sessionId}/groups`,
        {
            params,
        }
    );

    return response.data;
};


export const getAlerts = async (
    sessionId
) => {
    const response = await api.get(
        `/api/analysis/${sessionId}/alerts`
    );

    return response.data;
};


// ============================================
// PETS2009
// ============================================

export const getPetsViews = async () => {
    const response = await api.get(
        "/api/dataset/pets/views"
    );

    return response.data;
};


export const analyzePetsView = async (
    viewPath
) => {
    const response = await api.post(
        "/api/dataset/pets/analyze",
        null,
        {
            params: {
                view_path: viewPath,
            },
        }
    );

    return response.data;
};


// ============================================
// HEALTH
// ============================================

export const getHealth = async () => {
    const response = await api.get(
        "/health"
    );

    return response.data;
};


export default api;