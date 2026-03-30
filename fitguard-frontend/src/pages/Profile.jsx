import React, { useEffect, useState } from 'react';
import { UserCircle2, Trophy, Upload } from 'lucide-react';
import api from '../api/axios';
import { resolveApiUrl } from '../api/config';
import { useAuth } from '../context/AuthContext';

const emptyRecord = {
  metric_name: '',
  value: '',
  unit: '',
  achieved_on: new Date().toISOString().split('T')[0],
  notes: ''
};

const Profile = () => {
  const { user, refreshUser } = useAuth();
  const [profile, setProfile] = useState(null);
  const [recordForm, setRecordForm] = useState(emptyRecord);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const loadProfile = async () => {
    if (!user?.id) return;
    const response = await api.get('/profile/me');
    setProfile(response.data);
  };

  useEffect(() => {
    const run = async () => {
      try {
        await loadProfile();
      } catch (error) {
        console.error('Failed to load profile', error);
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [user?.id]);

  const updateField = (field, value) => {
    setProfile((prev) => ({ ...prev, [field]: value }));
  };

  const updateSetting = (field, value) => {
    setProfile((prev) => ({
      ...prev,
      sport_settings: { ...prev.sport_settings, [field]: value }
    }));
  };

  const saveProfile = async () => {
    setSaving(true);
    try {
      await api.put('/profile/me', {
        name: profile.name,
        age: parseInt(profile.age, 10),
        sport: profile.sport,
        weight: parseFloat(profile.weight),
        height: parseFloat(profile.height),
        injury_history: profile.profile?.injury_history || '',
        previous_injuries_count: parseInt(profile.profile?.previous_injuries_count || 0, 10),
        bio: profile.profile?.bio || '',
        intensity_low_threshold: parseFloat(profile.sport_settings?.intensity_low_threshold || 4),
        intensity_high_threshold: parseFloat(profile.sport_settings?.intensity_high_threshold || 7.5),
        hr_zone_easy_max: parseInt(profile.sport_settings?.hr_zone_easy_max || 130, 10),
        hr_zone_moderate_max: parseInt(profile.sport_settings?.hr_zone_moderate_max || 160, 10),
        hr_zone_hard_max: parseInt(profile.sport_settings?.hr_zone_hard_max || 185, 10)
      });
      await refreshUser();
      await loadProfile();
    } catch (error) {
      console.error('Failed to save profile', error);
    } finally {
      setSaving(false);
    }
  };

  const uploadAvatar = async (file) => {
    if (!file) return;
    const form = new FormData();
    form.append('avatar', file);
    try {
      await api.post('/profile/avatar', form, { headers: { 'Content-Type': 'multipart/form-data' } });
      await loadProfile();
      await refreshUser();
    } catch (error) {
      console.error('Failed to upload avatar', error);
    }
  };

  const createRecord = async (event) => {
    event.preventDefault();
    try {
      await api.post('/profile/records', {
        ...recordForm,
        value: parseFloat(recordForm.value)
      });
      setRecordForm(emptyRecord);
      await loadProfile();
    } catch (error) {
      console.error('Failed to add record', error);
    }
  };

  const deleteRecord = async (recordId) => {
    try {
      await api.delete(`/profile/records/${recordId}`);
      await loadProfile();
    } catch (error) {
      console.error('Failed to delete record', error);
    }
  };

  if (loading) {
    return <div className="animate-pulse h-64 rounded-2xl bg-slate-200" />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Athlete Profile</h1>
        <p className="text-slate-500 mt-1">Manage profile, injury history, personal records, and sport settings.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white border border-slate-200 rounded-2xl p-5 space-y-4">
          <h2 className="font-semibold text-slate-800 flex items-center gap-2">
            <UserCircle2 size={18} className="text-primary-600" /> Avatar
          </h2>
          <div className="w-28 h-28 rounded-full overflow-hidden border border-slate-200">
            {profile?.profile?.avatar_path ? (
              <img src={resolveApiUrl(profile.profile.avatar_path)} alt="avatar" className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-slate-400 bg-slate-50">No Image</div>
            )}
          </div>
          <label className="inline-flex items-center gap-2 rounded-xl border border-slate-300 px-3 py-2 cursor-pointer hover:bg-slate-50 text-sm">
            <Upload size={16} />
            Upload Photo
            <input type="file" accept="image/*" className="hidden" onChange={(e) => uploadAvatar(e.target.files?.[0])} />
          </label>
          <p className="text-xs text-slate-500">Supported: PNG, JPG, JPEG, WEBP.</p>
        </div>

        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl p-5 space-y-4">
          <h2 className="font-semibold text-slate-800">Profile Details</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input className="rounded-xl border border-slate-300 px-3 py-2" value={profile.name || ''} onChange={(e) => updateField('name', e.target.value)} placeholder="Name" />
            <input className="rounded-xl border border-slate-300 px-3 py-2" value={profile.sport || ''} onChange={(e) => updateField('sport', e.target.value)} placeholder="Sport" />
            <input className="rounded-xl border border-slate-300 px-3 py-2" type="number" value={profile.age || ''} onChange={(e) => updateField('age', e.target.value)} placeholder="Age" />
            <input className="rounded-xl border border-slate-300 px-3 py-2" type="number" step="0.1" value={profile.weight || ''} onChange={(e) => updateField('weight', e.target.value)} placeholder="Weight (kg)" />
            <input className="rounded-xl border border-slate-300 px-3 py-2" type="number" step="0.1" value={profile.height || ''} onChange={(e) => updateField('height', e.target.value)} placeholder="Height (cm)" />
            <input
              className="rounded-xl border border-slate-300 px-3 py-2"
              type="number"
              value={profile.profile?.previous_injuries_count || 0}
              onChange={(e) =>
                setProfile((prev) => ({
                  ...prev,
                  profile: { ...prev.profile, previous_injuries_count: e.target.value }
                }))
              }
              placeholder="Previous injuries"
            />
          </div>
          <textarea
            className="w-full rounded-xl border border-slate-300 px-3 py-2 min-h-20"
            value={profile.profile?.injury_history || ''}
            onChange={(e) =>
              setProfile((prev) => ({
                ...prev,
                profile: { ...prev.profile, injury_history: e.target.value }
              }))
            }
            placeholder="Injury history"
          />
          <textarea
            className="w-full rounded-xl border border-slate-300 px-3 py-2 min-h-20"
            value={profile.profile?.bio || ''}
            onChange={(e) =>
              setProfile((prev) => ({
                ...prev,
                profile: { ...prev.profile, bio: e.target.value }
              }))
            }
            placeholder="Bio"
          />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            <input
              className="rounded-xl border border-slate-300 px-3 py-2"
              type="number"
              step="0.1"
              value={profile.sport_settings?.intensity_low_threshold || 4}
              onChange={(e) => updateSetting('intensity_low_threshold', e.target.value)}
              placeholder="Low intensity threshold"
            />
            <input
              className="rounded-xl border border-slate-300 px-3 py-2"
              type="number"
              step="0.1"
              value={profile.sport_settings?.intensity_high_threshold || 7.5}
              onChange={(e) => updateSetting('intensity_high_threshold', e.target.value)}
              placeholder="High intensity threshold"
            />
            <input
              className="rounded-xl border border-slate-300 px-3 py-2"
              type="number"
              value={profile.sport_settings?.hr_zone_hard_max || 185}
              onChange={(e) => updateSetting('hr_zone_hard_max', e.target.value)}
              placeholder="HR hard max"
            />
          </div>
          <button
            onClick={saveProfile}
            disabled={saving}
            className="rounded-xl bg-primary-600 hover:bg-primary-700 text-white px-4 py-2.5 font-medium disabled:opacity-60"
          >
            {saving ? 'Saving...' : 'Save Profile'}
          </button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl p-5">
        <h2 className="font-semibold text-slate-800 flex items-center gap-2 mb-4">
          <Trophy size={18} className="text-amber-500" /> Personal Records
        </h2>
        <form onSubmit={createRecord} className="grid grid-cols-1 md:grid-cols-5 gap-3 mb-4">
          <input className="rounded-xl border border-slate-300 px-3 py-2" value={recordForm.metric_name} onChange={(e) => setRecordForm((prev) => ({ ...prev, metric_name: e.target.value }))} placeholder="Metric (e.g. Fastest 5K)" required />
          <input className="rounded-xl border border-slate-300 px-3 py-2" type="number" step="0.01" value={recordForm.value} onChange={(e) => setRecordForm((prev) => ({ ...prev, value: e.target.value }))} placeholder="Value" required />
          <input className="rounded-xl border border-slate-300 px-3 py-2" value={recordForm.unit} onChange={(e) => setRecordForm((prev) => ({ ...prev, unit: e.target.value }))} placeholder="Unit" />
          <input className="rounded-xl border border-slate-300 px-3 py-2" type="date" value={recordForm.achieved_on} onChange={(e) => setRecordForm((prev) => ({ ...prev, achieved_on: e.target.value }))} required />
          <button className="rounded-xl bg-slate-900 hover:bg-slate-800 text-white px-4 py-2">Add</button>
        </form>
        <div className="space-y-2">
          {(profile.personal_records || []).length ? (
            profile.personal_records.map((record) => (
              <div key={record.id} className="border border-slate-200 rounded-xl p-3 flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-800">{record.metric_name}</p>
                  <p className="text-sm text-slate-500">
                    {record.value} {record.unit || ''} on {record.achieved_on}
                  </p>
                </div>
                <button className="text-red-600 text-sm" onClick={() => deleteRecord(record.id)}>Delete</button>
              </div>
            ))
          ) : (
            <p className="text-slate-400">No personal records logged yet.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile;
