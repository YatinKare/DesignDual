import { env } from '$env/dynamic/public';

const DEFAULT_API_BASE_URL = 'http://localhost:8000';

export const API_BASE_URL = env.PUBLIC_API_BASE_URL?.trim() || DEFAULT_API_BASE_URL;
