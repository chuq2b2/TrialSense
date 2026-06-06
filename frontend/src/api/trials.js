import axios from "axios";

const api = axios.create({
  baseURL: "/api",
});

export async function lookupTrial(input) {
  const { data } = await api.post("/trials/lookup", { input });
  return data;
}

export async function matchPatients(trial) {
  const { data } = await api.post("/trials/match", trial, {
    timeout: 300_000,
  });
  return data;
}
