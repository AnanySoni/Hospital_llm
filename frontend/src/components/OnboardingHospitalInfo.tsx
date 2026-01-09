import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDebounce } from '../hooks/useDebounce';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const PUBLIC_BASE_URL = process.env.REACT_APP_PUBLIC_BASE_URL || 'https://yourdomain.com';

type SlugStatus = {
  loading: boolean;
  valid: boolean;
  available: boolean;
  reason: string | null;
  suggestions: string[];
  lastChecked: number;
};

const OnboardingHospitalInfo: React.FC = () => {
  const navigate = useNavigate();

  const [hospitalName, setHospitalName] = useState('');
  const [slug, setSlug] = useState('');
  const [slugManuallyEdited, setSlugManuallyEdited] = useState(false);

  const [address, setAddress] = useState('');
  const [phone, setPhone] = useState('');
  const [website, setWebsite] = useState('');

  const [slugStatus, setSlugStatus] = useState<SlugStatus>({
    loading: false,
    valid: false,
    available: false,
    reason: null,
    suggestions: [],
    lastChecked: 0,
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Basic auth guard: ensure we have an access token
  useEffect(() => {
    const token = window.localStorage.getItem('access_token');
    if (!token) {
      navigate('/onboarding/register');
    }
  }, [navigate]);

  // Auto-generate slug from hospital name when not manually edited
  const handleHospitalNameChange = (value: string) => {
    setHospitalName(value);
    if (!slugManuallyEdited) {
      const base = value
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '');
      setSlug(base);
    }
  };

  const handleSlugChange = (value: string) => {
    // Auto-format: lowercase, remove spaces
    const formatted = value.toLowerCase().replace(/\s+/g, '-');
    setSlug(formatted);
    setSlugManuallyEdited(true);
  };

  const handleGenerateSlug = () => {
    const base = hospitalName
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
    setSlug(base);
    setSlugManuallyEdited(false);
  };

  // Debounce slug for API calls
  const debouncedSlug = useDebounce(slug, 500);

  // Debounced slug validation
  useEffect(() => {
    if (!debouncedSlug) {
      setSlugStatus({
        loading: false,
        valid: false,
        available: false,
        reason: 'empty',
        suggestions: [],
        lastChecked: Date.now(),
      });
      return;
    }

    const checkSlug = async () => {
      try {
        setSlugStatus((s) => ({ ...s, loading: true }));
        const res = await fetch(
          `${API_BASE}/onboarding/slug/check?slug=${encodeURIComponent(debouncedSlug)}`
        );
        const data = await res.json();
        setSlugStatus({
          loading: false,
          valid: !!data.valid,
          available: !!data.available,
          reason: data.reason ?? null,
          suggestions: Array.isArray(data.suggestions) ? data.suggestions : [],
          lastChecked: Date.now(),
        });
      } catch {
        setSlugStatus({
          loading: false,
          valid: false,
          available: false,
          reason: 'network_error',
          suggestions: [],
          lastChecked: Date.now(),
        });
      }
    };

    checkSlug();
  }, [debouncedSlug]);

  const canContinue =
    hospitalName.trim().length >= 2 &&
    slug.trim().length >= 3 &&
    slugStatus.valid &&
    slugStatus.available &&
    !isSubmitting;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canContinue) return;

    setError(null);
    setSuccess(null);
    setIsSubmitting(true);

    try {
      const token = window.localStorage.getItem('access_token');
      if (!token) {
        navigate('/onboarding/register');
        return;
      }

      const trimmedWebsite = website.trim();
      const normalizedWebsite =
        trimmedWebsite && !/^https?:\/\//i.test(trimmedWebsite)
          ? `https://${trimmedWebsite}`
          : trimmedWebsite || undefined;

      const payload = {
        hospital_name: hospitalName.trim(),
        slug: slug.trim(),
        address: address.trim() || undefined,
        phone: phone.trim() || undefined,
        website: normalizedWebsite,
      };

      const res = await fetch(`${API_BASE}/onboarding/hospital-info`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to save hospital information.');
      }

      setSuccess('Hospital information saved. Redirecting to completion screen...');
      navigate('/onboarding/complete');
    } catch (err: any) {
      setError(err.message || 'Failed to save hospital information.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4 py-8">
      <div className="max-w-2xl w-full bg-gray-900/80 border border-gray-800 rounded-2xl shadow-xl p-6 sm:p-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-xs text-blue-300 uppercase tracking-wider mb-1">
              Step 3 of 3
            </p>
            <h1 className="text-xl sm:text-2xl font-semibold text-white">
              Hospital information
            </h1>
            <p className="text-gray-400 text-sm mt-1">
              Tell us about your hospital and choose your unique URL.
            </p>
          </div>
          <button
            type="button"
            onClick={() => navigate('/onboarding/register')}
            className="text-xs text-gray-400 hover:text-gray-200"
          >
            ← Back
          </button>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Hospital name
            </label>
            <input
              autoFocus
              type="text"
              value={hospitalName}
              onChange={(e) => handleHospitalNameChange(e.target.value)}
              required
              className="w-full px-3 py-2 rounded-lg bg-gray-900 border border-gray-700 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="City General Hospital"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Hospital slug (URL identifier)
              <span className="text-gray-500 text-xs ml-1">
                ({slug.length}/50)
              </span>
            </label>
            <div className="flex items-center gap-2">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={slug}
                  onChange={(e) => handleSlugChange(e.target.value)}
                  required
                  className={`w-full px-3 py-2 pr-10 rounded-lg bg-gray-900 border text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    slugStatus.loading
                      ? 'border-gray-600'
                      : !slug
                      ? 'border-gray-700'
                      : slugStatus.valid && slugStatus.available
                      ? 'border-green-500'
                      : !slugStatus.valid
                      ? 'border-red-500'
                      : 'border-yellow-500'
                  }`}
                  placeholder="city-general-hospital"
                  maxLength={50}
                />
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  {slugStatus.loading ? (
                    <svg
                      className="animate-spin h-4 w-4 text-gray-400"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                  ) : slug && slugStatus.valid && slugStatus.available ? (
                    <svg
                      className="h-4 w-4 text-green-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  ) : slug && (!slugStatus.valid || !slugStatus.available) ? (
                    <svg
                      className={`h-4 w-4 ${
                        !slugStatus.valid ? 'text-red-400' : 'text-yellow-400'
                      }`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  ) : null}
                </div>
              </div>
              <button
                type="button"
                onClick={handleGenerateSlug}
                disabled={!hospitalName.trim()}
                className="px-3 py-2 text-xs text-blue-400 hover:text-blue-300 disabled:text-gray-600 disabled:cursor-not-allowed border border-gray-700 rounded-lg hover:border-gray-600 transition-colors"
              >
                Generate
              </button>
            </div>
            
            {/* Status message */}
            {slug && (
              <p
                className={`mt-1 text-xs ${
                  slugStatus.loading
                    ? 'text-gray-400'
                    : slugStatus.valid && slugStatus.available
                    ? 'text-green-400'
                    : !slugStatus.valid
                    ? 'text-red-400'
                    : 'text-yellow-400'
                }`}
              >
                {slugStatus.loading
                  ? 'Checking availability...'
                  : slugStatus.valid && slugStatus.available
                  ? '✓ Available'
                  : !slugStatus.valid
                  ? `✗ Invalid format${slugStatus.reason ? `: ${slugStatus.reason}` : ''}`
                  : slugStatus.reason === 'taken'
                  ? '✗ Already taken'
                  : slugStatus.reason === 'reserved'
                  ? '✗ Reserved word'
                  : '✗ Unavailable'}
              </p>
            )}
            
            {/* Auto-display suggestions when invalid/taken */}
            {slugStatus.suggestions.length > 0 && (
              <div className="mt-2 p-3 bg-gray-800 rounded border border-gray-700">
                <p className="text-xs text-gray-400 mb-2">
                  {slugStatus.reason === 'taken'
                    ? 'Suggestions:'
                    : slugStatus.reason === 'reserved'
                    ? 'Alternative slugs:'
                    : 'Try these:'}
                </p>
                <div className="flex flex-wrap gap-2">
                  {slugStatus.suggestions.map((s, idx) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => {
                        setSlug(s);
                        setSlugManuallyEdited(true);
                      }}
                      className={`text-xs px-3 py-1.5 rounded border transition-colors ${
                        idx === 0
                          ? 'bg-blue-900/30 border-blue-700 text-blue-300 hover:bg-blue-900/50'
                          : 'bg-gray-700 border-gray-600 text-gray-200 hover:bg-gray-600'
                      }`}
                    >
                      {idx === 0 && 'Recommended: '}
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            <p className="mt-2 text-xs text-gray-400">
              Your chat URL will be:{' '}
              <span className="font-mono text-gray-200">
                {PUBLIC_BASE_URL}/h/{slug || '<slug>'}
              </span>
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Address (optional)
            </label>
            <textarea
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 rounded-lg bg-gray-900 border border-gray-700 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="123 Healthcare Street, Medical City"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Phone (optional)
              </label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-gray-900 border border-gray-700 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="+91-9876543210"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Website (optional)
              </label>
              <input
                type="text"
                value={website}
                onChange={(e) => setWebsite(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-gray-900 border border-gray-700 text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="https://citygeneral.com"
              />
            </div>
          </div>

          {error && (
            <div className="text-sm text-red-400 bg-red-950/40 border border-red-800 px-3 py-2 rounded-lg">
              {error}
            </div>
          )}

          {success && (
            <div className="text-sm text-green-400 bg-emerald-950/40 border border-emerald-800 px-3 py-2 rounded-lg">
              {success}
            </div>
          )}

          <button
            type="submit"
            disabled={!canContinue}
            className="w-full mt-2 inline-flex items-center justify-center px-4 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-500 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? 'Saving...' : 'Continue'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default OnboardingHospitalInfo;


