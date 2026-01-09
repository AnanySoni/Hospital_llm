import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// Types for hospital context
export interface HospitalData {
  id: string;
  slug: string;
  name?: string;
  logo?: string;
  [key: string]: any;
}

interface HospitalContextProps {
  hospital: HospitalData | null;
  setHospital: (hospital: HospitalData | null) => void;
  switchHospital: (slug: string) => Promise<void>;
  loading: boolean;
}

const HospitalContext = createContext<HospitalContextProps | undefined>(undefined);

// Simple in-memory cache for hospital data
const hospitalCache: { [slug: string]: HospitalData } = {};

export const HospitalProvider = ({ slug, children }: { slug: string; children: ReactNode }) => {
  const [hospital, setHospital] = useState<HospitalData | null>(null);
  const [loading, setLoading] = useState(false);

  // Fetch hospital data by slug, with cache
  const fetchHospital = async (slug: string) => {
    console.log(`[HospitalContext] Fetching hospital for slug: ${slug}`);
    if (hospitalCache[slug]) {
      console.log(`[HospitalContext] Cache hit for slug: ${slug}`);
      setHospital(hospitalCache[slug]);
      return;
    }
    setLoading(true);
    try {
      // Use public endpoint for hospital lookup (no auth required)
      console.log(`[HospitalContext] Making API call to: /hospitals/by-slug/${slug}`);
      const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
      const res = await fetch(`${API_BASE}/hospitals/by-slug/${slug}`);
      console.log(`[HospitalContext] Response status: ${res.status}`);
      if (!res.ok) throw new Error('Hospital not found');
      const data = await res.json();
      console.log(`[HospitalContext] Hospital data received:`, data);
      // The backend returns {id, slug, name}, but we want to keep the same shape
      hospitalCache[slug] = data;
      setHospital(data);
    } catch (err) {
      console.error(`[HospitalContext] Error fetching hospital for slug ${slug}:`, err);
      setHospital(null);
    } finally {
      setLoading(false);
    }
  };

  // Switch hospital by slug
  const switchHospital = async (newSlug: string) => {
    await fetchHospital(newSlug);
  };

  useEffect(() => {
    if (slug) fetchHospital(slug);
  }, [slug]);

  return (
    <HospitalContext.Provider value={{ hospital, setHospital, switchHospital, loading }}>
      {children}
    </HospitalContext.Provider>
  );
};

// Hook to use hospital context
export const useHospital = () => {
  const ctx = useContext(HospitalContext);
  if (!ctx) throw new Error('useHospital must be used within a HospitalProvider');
  return ctx;
};
