import React, { useEffect, useState } from 'react';
import { Users, FileDown, Shield } from 'lucide-react';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';

const defaultTemplate = [
  { day_offset: 0, session_name: 'Aerobic Base', duration_hrs: 1.2, intensity_target: 5.5, distance_target_km: 6, is_rest_day: false, notes: 'Steady session' },
  { day_offset: 1, session_name: 'Strength', duration_hrs: 1.0, intensity_target: 6.5, distance_target_km: 0, is_rest_day: false, notes: 'Lower-body and core' },
  { day_offset: 2, session_name: 'Recovery', duration_hrs: 0.6, intensity_target: 2.5, distance_target_km: 0, is_rest_day: true, notes: 'Mobility + breathing' },
  { day_offset: 3, session_name: 'Intervals', duration_hrs: 1.1, intensity_target: 8.0, distance_target_km: 7, is_rest_day: false, notes: '4 x 4 min hard' },
  { day_offset: 4, session_name: 'Skill Session', duration_hrs: 1.0, intensity_target: 6.0, distance_target_km: 4, is_rest_day: false, notes: 'Technique focus' },
  { day_offset: 5, session_name: 'Endurance', duration_hrs: 1.5, intensity_target: 7.0, distance_target_km: 9, is_rest_day: false, notes: 'Sustained pace' },
  { day_offset: 6, session_name: 'Rest Day', duration_hrs: 0.4, intensity_target: 2.0, distance_target_km: 0, is_rest_day: true, notes: 'Walk + stretch' }
];

const CoachAdmin = () => {
  const { user, refreshUser } = useAuth();
  const [allAthletes, setAllAthletes] = useState([]);
  const [assignedAthletes, setAssignedAthletes] = useState([]);
  const [teamRisk, setTeamRisk] = useState([]);
  const [selectedAthletes, setSelectedAthletes] = useState([]);
  const [bulkTargets, setBulkTargets] = useState([]);
  const [weekStart, setWeekStart] = useState(new Date().toISOString().split('T')[0]);
  const [isLoading, setIsLoading] = useState(true);

  const isCoach = user?.profile?.account_type === 'coach';

  const loadData = async () => {
    if (!isCoach) return;
    const [allRes, assignedRes, riskRes] = await Promise.all([
      api.get('/athletes/all'),
      api.get('/coach/assignments'),
      api.get('/coach/team/risk')
    ]);
    setAllAthletes(allRes.data || []);
    setAssignedAthletes(assignedRes.data || []);
    setTeamRisk(riskRes.data || []);
  };

  useEffect(() => {
    const run = async () => {
      try {
        if (isCoach) {
          await loadData();
        }
      } catch (error) {
        console.error('Failed loading coach data', error);
      } finally {
        setIsLoading(false);
      }
    };
    run();
  }, [isCoach]);

  const upgradeCoach = async () => {
    try {
      await api.post('/coach/account/upgrade');
      await refreshUser();
    } catch (error) {
      console.error('Failed to upgrade account', error);
    }
  };

  const assignAthletes = async () => {
    try {
      await api.post('/coach/assignments', { athlete_ids: selectedAthletes });
      setSelectedAthletes([]);
      await loadData();
    } catch (error) {
      console.error('Failed assigning athletes', error);
    }
  };

  const bulkAssign = async () => {
    try {
      await api.post('/coach/plans/bulk-assign', {
        athlete_ids: bulkTargets,
        week_start: weekStart,
        sessions: defaultTemplate
      });
      await loadData();
    } catch (error) {
      console.error('Failed bulk assignment', error);
    }
  };

  const downloadReport = async (athleteId) => {
    try {
      const response = await api.get(`/coach/report/${athleteId}/pdf`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `fitguard_report_${athleteId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download report', error);
    }
  };

  if (isLoading) {
    return <div className="animate-pulse h-64 rounded-2xl bg-slate-200" />;
  }

  if (!isCoach) {
    return (
      <div className="max-w-xl mx-auto bg-white border border-slate-200 rounded-2xl p-6 text-center">
        <Shield className="mx-auto text-primary-600" size={38} />
        <h1 className="text-2xl font-bold text-slate-900 mt-3">Coach Account Required</h1>
        <p className="text-slate-500 mt-2">
          Upgrade your account to coach mode to manage multiple athletes, compare team risk, and bulk assign plans.
        </p>
        <button
          onClick={upgradeCoach}
          className="mt-5 rounded-xl bg-primary-600 hover:bg-primary-700 text-white px-4 py-2.5 font-medium"
        >
          Upgrade to Coach
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Coach / Admin View</h1>
        <p className="text-slate-500 mt-1">Manage team athletes, compare risk, export reports, and bulk assign plans.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-slate-200 rounded-2xl p-5">
          <h2 className="font-semibold text-slate-800 flex items-center gap-2 mb-3">
            <Users size={18} className="text-primary-600" /> Assign Athletes
          </h2>
          <div className="max-h-52 overflow-auto space-y-2">
            {allAthletes.map((athlete) => (
              <label key={athlete.id} className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={selectedAthletes.includes(athlete.id)}
                  onChange={(e) =>
                    setSelectedAthletes((prev) =>
                      e.target.checked ? [...prev, athlete.id] : prev.filter((id) => id !== athlete.id)
                    )
                  }
                />
                {athlete.name} ({athlete.sport})
              </label>
            ))}
          </div>
          <button onClick={assignAthletes} className="mt-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-white px-4 py-2.5">
            Save Assignments
          </button>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-5">
          <h2 className="font-semibold text-slate-800 mb-3">Bulk Training Plan Assignment</h2>
          <input
            type="date"
            className="rounded-xl border border-slate-300 px-3 py-2 text-sm mb-3"
            value={weekStart}
            onChange={(e) => setWeekStart(e.target.value)}
          />
          <div className="max-h-40 overflow-auto space-y-2 border border-slate-200 rounded-xl p-3">
            {assignedAthletes.map((athlete) => (
              <label key={athlete.id} className="flex items-center gap-2 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={bulkTargets.includes(athlete.id)}
                  onChange={(e) =>
                    setBulkTargets((prev) =>
                      e.target.checked ? [...prev, athlete.id] : prev.filter((id) => id !== athlete.id)
                    )
                  }
                />
                {athlete.name}
              </label>
            ))}
          </div>
          <button onClick={bulkAssign} className="mt-4 rounded-xl bg-primary-600 hover:bg-primary-700 text-white px-4 py-2.5">
            Assign Template Plan
          </button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl p-5">
        <h2 className="font-semibold text-slate-800 mb-4">Team Risk Comparison</h2>
        <div className="space-y-3">
          {teamRisk.length ? (
            teamRisk.map((row) => (
              <div key={row.athlete_id} className="border border-slate-200 rounded-xl p-3 flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-800">{row.athlete_name}</p>
                  <p className="text-sm text-slate-500">
                    Risk: {row.risk_level} ({row.risk_score ?? 'N/A'}%) | Fatigue level: {row.fatigue_level ?? 'N/A'}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => downloadReport(row.athlete_id)}
                  className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700 text-sm"
                >
                  <FileDown size={16} /> Export PDF
                </button>
              </div>
            ))
          ) : (
            <p className="text-slate-400">No assigned athletes yet.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default CoachAdmin;
