import React, { useEffect, useMemo, useState } from 'react';
import { Brain, RefreshCcw, Sparkles, ShieldAlert, DatabaseZap } from 'lucide-react';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';

const SmartCoach = () => {
  const { user } = useAuth();
  const [prediction, setPrediction] = useState(null);
  const [recommendation, setRecommendation] = useState(null);
  const [modelMetrics, setModelMetrics] = useState(null);
  const [isPredicting, setIsPredicting] = useState(false);
  const [isCoaching, setIsCoaching] = useState(false);
  const [isRetraining, setIsRetraining] = useState(false);
  const [error, setError] = useState('');

  const loadExisting = async () => {
    if (!user?.id) return;
    const [predRes, recRes, metricsRes] = await Promise.all([
      api.get(`/predict/injury/latest/${user.id}`).catch(() => ({ data: {} })),
      api.get(`/coach/recommend/${user.id}`).catch(() => ({ data: {} })),
      api.get('/predict/model/metrics').catch(() => ({ data: {} }))
    ]);
    setPrediction(predRes.data?.prediction || null);
    setRecommendation(recRes.data?.recommendation || null);
    setModelMetrics(metricsRes.data?.dashboard || null);
  };

  useEffect(() => {
    loadExisting();
  }, [user?.id]);

  const runPrediction = async () => {
    setIsPredicting(true);
    setError('');
    try {
      const logRes = await api.get(`/training/latest/${user.id}`);
      const log = logRes.data?.log;

      const features = {
        Player_Age: user.age || 25,
        Player_Weight: user.weight || 70,
        Player_Height: user.height || 175,
        Previous_Injuries: user.profile?.previous_injuries_count || 0,
        Training_Intensity: log?.intensity ?? 5,
        Recovery_Time: 3
      };
      const predRes = await api.post('/predict/injury', { features });
      setPrediction(predRes.data.prediction);
      setModelMetrics((prev) => ({ ...(prev || {}), metrics: predRes.data.model_metrics || prev?.metrics }));

      setIsCoaching(true);
      const recRes = await api.get(`/coach/recommend/${user.id}`);
      setRecommendation(recRes.data.recommendation);
    } catch (err) {
      setError('Failed to generate prediction. Check backend configuration.');
      console.error(err);
    } finally {
      setIsPredicting(false);
      setIsCoaching(false);
    }
  };

  const retrainModel = async () => {
    setIsRetraining(true);
    try {
      await api.post('/predict/model/retrain', {});
      await loadExisting();
    } catch (err) {
      setError('Model retraining failed.');
      console.error(err);
    } finally {
      setIsRetraining(false);
    }
  };

  const featureImportance = useMemo(() => {
    let obj = modelMetrics?.feature_importance || {};
    if (prediction?.insight?.feature_importance) {
      try {
        obj = JSON.parse(prediction.insight.feature_importance);
      } catch {
        obj = modelMetrics?.feature_importance || {};
      }
    }
    return Object.entries(obj).sort((a, b) => b[1] - a[1]).slice(0, 6);
  }, [prediction?.insight?.feature_importance, modelMetrics?.feature_importance]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
            <Brain className="text-primary-600" /> AI Smart Coach
          </h1>
          <p className="text-slate-500 mt-1">Random Forest risk prediction with confidence intervals and week-long coaching plan.</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={runPrediction}
            disabled={isPredicting || isCoaching}
            className="rounded-xl bg-primary-600 hover:bg-primary-700 text-white px-4 py-2.5 inline-flex items-center gap-2 disabled:opacity-60"
          >
            <Sparkles size={16} />
            {isPredicting ? 'Predicting...' : isCoaching ? 'Coaching...' : 'Scan New Data'}
          </button>
          <button
            onClick={retrainModel}
            disabled={isRetraining}
            className="rounded-xl border border-slate-300 hover:bg-slate-50 px-4 py-2.5 inline-flex items-center gap-2 disabled:opacity-60"
          >
            <DatabaseZap size={16} />
            {isRetraining ? 'Retraining...' : 'Retrain Model'}
          </button>
        </div>
      </div>

      {error && <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3">{error}</div>}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-slate-200 rounded-2xl p-6">
          <h2 className="font-semibold text-slate-800 mb-4">Current Injury Risk</h2>
          {prediction ? (
            <div className="space-y-3">
              <div
                className={`w-36 h-36 rounded-full mx-auto flex items-center justify-center text-white text-3xl font-bold
                  ${prediction.risk_level === 'High' ? 'bg-red-500' : prediction.risk_level === 'Medium' ? 'bg-amber-500' : 'bg-emerald-500'}`}
              >
                {prediction.risk_score}%
              </div>
              <p className="text-center text-slate-700 font-semibold uppercase">{prediction.risk_level} Risk</p>
              <p className="text-sm text-slate-500 text-center">Algorithm: {prediction.algorithm_used}</p>
              {prediction.insight && (
                <p className="text-sm text-slate-600 text-center">
                  Confidence interval: {prediction.insight.confidence_lower}% - {prediction.insight.confidence_upper}%
                </p>
              )}
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-slate-400">
              No prediction yet.
            </div>
          )}
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-6">
          <h2 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <ShieldAlert size={18} className="text-orange-500" /> Feature Importance
          </h2>
          {featureImportance.length ? (
            <div className="space-y-2">
              {featureImportance.map(([feature, value]) => (
                <div key={feature}>
                  <div className="flex justify-between text-sm text-slate-700 mb-1">
                    <span>{feature}</span>
                    <span>{(value * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full">
                    <div className="h-full bg-primary-600 rounded-full" style={{ width: `${Math.min(100, value * 100)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-400">Feature importance available after first model run.</p>
          )}
          {modelMetrics?.metrics && (
            <div className="mt-5 rounded-xl bg-slate-50 p-3 text-sm text-slate-600">
              Precision: {modelMetrics.metrics.precision} | Recall: {modelMetrics.metrics.recall} | F1: {modelMetrics.metrics.f1_score}
            </div>
          )}
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl p-6">
        <h2 className="font-semibold text-slate-800 mb-4">Claude Weekly Training Plan</h2>
        {isCoaching ? (
          <div className="h-28 flex items-center justify-center text-primary-600">
            <RefreshCcw className="animate-spin mr-2" size={18} />
            Generating week-long plan...
          </div>
        ) : recommendation ? (
          <pre className="whitespace-pre-wrap text-sm leading-relaxed bg-primary-50 border border-primary-100 rounded-xl p-4 text-slate-800">
            {recommendation.message}
          </pre>
        ) : (
          <p className="text-slate-400">Run a prediction to generate your weekly coaching plan.</p>
        )}
      </div>
    </div>
  );
};

export default SmartCoach;
