import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Switch,
  FormControlLabel,
  Slider,
  Button,
  Alert,
  LinearProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  IconButton,
  TextField,
  MenuItem,
  Tabs,
  Tab
} from '@mui/material';
import {
  Memory,
  Speed,
  Settings,
  Refresh,
  PlayArrow,
  Stop,
  Clear,
  ExpandMore,
  Info,
  TrendingUp,
  Computer,
  Storage,
  Timeline,
  Assignment,
  Group,
  QueryStats,
  Tune
} from '@mui/icons-material';
import { toast } from 'react-hot-toast';

interface Worker {
  id: string;
  type: string;
  status: string;
  tasks_completed: number;
  tasks_failed: number;
  cpu_usage: number;
  memory_usage: number;
  current_task?: string;
}

interface Task {
  id: string;
  function_name: string;
  status: string;
  priority: number;
  created_at: number;
  started_at?: number;
  completed_at?: number;
  processing_time?: number;
  worker_id?: string;
  error?: string;
  retry_count: number;
}

interface DistributedConfig {
  max_workers: number;
  worker_type: string;
  task_timeout: number;
  enable_load_balancing: boolean;
  enable_auto_scaling: boolean;
  min_workers: number;
  scale_up_threshold: number;
  scale_down_threshold: number;
}

interface DistributedStatus {
  is_running: boolean;
  workers: {
    total: number;
    active: number;
    idle: number;
    details: Worker[];
  };
  tasks: {
    total: number;
    pending: number;
    processing: number;
    completed: number;
    failed: number;
    cancelled: number;
  };
  metrics: {
    tasks_submitted: number;
    tasks_completed: number;
    tasks_failed: number;
    avg_processing_time: number;
    queue_size: number;
    active_workers: number;
    throughput: number;
    error_rate: number;
  };
  health: {
    status: string;
    uptime: number;
    queue_health: string;
    worker_health: string;
    error_rate_health: string;
  };
}

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

const DistributedProcessing: React.FC = () => {
  const [config, setConfig] = useState<DistributedConfig | null>(null);
  const [status, setStatus] = useState<DistributedStatus | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  
  // Task submission state
  const [showTaskDialog, setShowTaskDialog] = useState(false);
  const [taskForm, setTaskForm] = useState({
    function_name: '',
    priority: 'normal',
    timeout: 30,
    args: '[]',
    kwargs: '{}'
  });
  const [submittingTask, setSubmittingTask] = useState(false);

  const fetchDistributedData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [statusRes, configRes, tasksRes, workersRes, metricsRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/distributed/status`),
        fetch(`${BACKEND_URL}/api/distributed/config`),
        fetch(`${BACKEND_URL}/api/distributed/tasks?limit=50`),
        fetch(`${BACKEND_URL}/api/distributed/workers`),
        fetch(`${BACKEND_URL}/api/distributed/metrics`)
      ]);

      if (statusRes.ok) {
        const statusData = await statusRes.json();
        if (statusData.success) setStatus(statusData.status);
      }

      if (configRes.ok) {
        const configData = await configRes.json();
        if (configData.success) setConfig(configData.config);
      }

      if (tasksRes.ok) {
        const tasksData = await tasksRes.json();
        if (tasksData.success) setTasks(tasksData.tasks);
      }

      if (workersRes.ok) {
        const workersData = await workersRes.json();
        if (workersData.success) setWorkers(workersData.workers);
      }

      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        if (metricsData.success) setMetrics(metricsData.metrics);
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      toast.error(`Failed to load distributed processing data: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateConfig = useCallback(async (updates: Partial<DistributedConfig>) => {
    try {
      setUpdating(true);
      
      const response = await fetch(`${BACKEND_URL}/api/distributed/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });

      const data = await response.json();
      
      if (data.success) {
        setConfig(data.new_config.config);
        toast.success('Configuration updated successfully');
        setTimeout(fetchDistributedData, 1000);
      } else {
        throw new Error(data.message || 'Failed to update configuration');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      toast.error(`Failed to update configuration: ${errorMessage}`);
    } finally {
      setUpdating(false);
    }
  }, [fetchDistributedData]);

  const startDistributedProcessing = useCallback(async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/distributed/start`, {
        method: 'POST'
      });

      const data = await response.json();
      
      if (data.success) {
        toast.success(data.message);
        setTimeout(fetchDistributedData, 2000);
      } else {
        throw new Error(data.message || 'Failed to start distributed processing');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      toast.error(`Failed to start: ${errorMessage}`);
    }
  }, [fetchDistributedData]);

  const stopDistributedProcessing = useCallback(async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/distributed/stop`, {
        method: 'POST'
      });

      const data = await response.json();
      
      if (data.success) {
        toast.success(data.message);
        setTimeout(fetchDistributedData, 2000);
      } else {
        throw new Error(data.message || 'Failed to stop distributed processing');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      toast.error(`Failed to stop: ${errorMessage}`);
    }
  }, [fetchDistributedData]);

  const submitTask = useCallback(async () => {
    try {
      setSubmittingTask(true);
      
      let args, kwargs;
      try {
        args = JSON.parse(taskForm.args);
        kwargs = JSON.parse(taskForm.kwargs);
      } catch (e) {
        throw new Error('Invalid JSON in args or kwargs');
      }

      const response = await fetch(`${BACKEND_URL}/api/distributed/tasks/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          function_name: taskForm.function_name,
          args,
          kwargs,
          priority: taskForm.priority,
          timeout: taskForm.timeout
        })
      });

      const data = await response.json();
      
      if (data.success) {
        toast.success(`Task submitted: ${data.task_id}`);
        setShowTaskDialog(false);
        setTaskForm({
          function_name: '',
          priority: 'normal',
          timeout: 30,
          args: '[]',
          kwargs: '{}'
        });
        fetchDistributedData();
      } else {
        throw new Error(data.message || 'Failed to submit task');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      toast.error(`Failed to submit task: ${errorMessage}`);
    } finally {
      setSubmittingTask(false);
    }
  }, [taskForm, fetchDistributedData]);

  useEffect(() => {
    fetchDistributedData();
  }, [fetchDistributedData]);

  // Auto-refresh every 10 seconds
  useEffect(() => {
    const interval = setInterval(fetchDistributedData, 10000);
    return () => clearInterval(interval);
  }, [fetchDistributedData]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        <Typography variant="h6">Distributed Processing Error</Typography>
        <Typography>{error}</Typography>
        <Button onClick={fetchDistributedData} startIcon={<Refresh />} sx={{ mt: 1 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours}h ${minutes}m ${secs}s`;
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'good':
      case 'running':
      case 'completed':
        return 'success';
      case 'warning':
      case 'concerning':
      case 'processing':
        return 'warning';
      case 'error':
      case 'failed':
      case 'stopped':
        return 'error';
      default:
        return 'default';
    }
  };

  const getPriorityColor = (priority: number) => {
    switch (priority) {
      case 4: return '#f44336'; // Critical
      case 3: return '#ff9800'; // High
      case 2: return '#2196f3'; // Normal
      case 1: return '#4caf50'; // Low
      default: return '#9e9e9e';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Computer />
          Distributed Processing
        </Typography>
        <Box>
          <Button 
            onClick={fetchDistributedData} 
            startIcon={<Refresh />} 
            disabled={loading}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          {status?.is_running ? (
            <Button 
              onClick={stopDistributedProcessing}
              startIcon={<Stop />}
              color="error"
              variant="outlined"
              sx={{ mr: 1 }}
            >
              Stop
            </Button>
          ) : (
            <Button 
              onClick={startDistributedProcessing}
              startIcon={<PlayArrow />}
              color="success"
              variant="outlined"
              sx={{ mr: 1 }}
            >
              Start
            </Button>
          )}
          <Button 
            onClick={() => setShowTaskDialog(true)}
            startIcon={<Assignment />}
            variant="contained"
          >
            Submit Task
          </Button>
        </Box>
      </Box>

      {/* System Status Overview */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' }, gap: 3, mb: 3 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Computer />
              System Status
            </Typography>
            {status && (
              <Box>
                <Chip 
                  label={status.is_running ? 'Running' : 'Stopped'} 
                  color={status.is_running ? 'success' : 'error'} 
                  sx={{ mb: 1 }}
                />
                <Typography variant="body2" color="text.secondary">
                  Health: <Chip label={status.health.status} color={getStatusColor(status.health.status)} size="small" />
                </Typography>
                {status.health.uptime > 0 && (
                  <Typography variant="body2" color="text.secondary">
                    Uptime: {formatUptime(status.health.uptime)}
                  </Typography>
                )}
              </Box>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Group />
              Workers
            </Typography>
            {status && (
              <Box>
                <Typography variant="h4" color="primary">
                  {status.workers.total}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active: {status.workers.active} | Idle: {status.workers.idle}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Health: <Chip label={status.health.worker_health} color={getStatusColor(status.health.worker_health)} size="small" />
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Assignment />
              Tasks
            </Typography>
            {status && (
              <Box>
                <Typography variant="h4" color="primary">
                  {status.tasks.total}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Processing: {status.tasks.processing} | Pending: {status.tasks.pending}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Queue: <Chip label={status.health.queue_health} color={getStatusColor(status.health.queue_health)} size="small" />
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <QueryStats />
              Performance
            </Typography>
            {status && (
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Throughput: {status.metrics.throughput} tasks/min
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Avg Time: {status.metrics.avg_processing_time.toFixed(2)}s
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Error Rate: <Chip 
                    label={`${status.metrics.error_rate.toFixed(1)}%`} 
                    color={getStatusColor(status.health.error_rate_health)} 
                    size="small" 
                  />
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>

      {/* Tabbed Interface */}
      <Card>
        <CardContent>
          <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
            <Tab label="Configuration" icon={<Settings />} />
            <Tab label="Workers" icon={<Group />} />
            <Tab label="Tasks" icon={<Assignment />} />
            <Tab label="Metrics" icon={<QueryStats />} />
          </Tabs>

          {/* Configuration Tab */}
          {activeTab === 0 && config && (
            <Box>
              <Typography variant="h6" gutterBottom>
                System Configuration
                {updating && <CircularProgress size={20} sx={{ ml: 1 }} />}
              </Typography>

              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 3 }}>
                <Box>
                  <Box sx={{ mb: 3 }}>
                    <Typography gutterBottom>Max Workers</Typography>
                    <Slider
                      value={config.max_workers}
                      onChange={(_, value) => updateConfig({ max_workers: value as number })}
                      min={1}
                      max={16}
                      marks
                      valueLabelDisplay="auto"
                      disabled={updating}
                    />
                  </Box>

                  <Box sx={{ mb: 3 }}>
                    <Typography gutterBottom>Min Workers</Typography>
                    <Slider
                      value={config.min_workers}
                      onChange={(_, value) => updateConfig({ min_workers: value as number })}
                      min={1}
                      max={config.max_workers}
                      marks
                      valueLabelDisplay="auto"
                      disabled={updating}
                    />
                  </Box>

                  <Box sx={{ mb: 3 }}>
                    <Typography gutterBottom>Task Timeout (seconds)</Typography>
                    <Slider
                      value={config.task_timeout}
                      onChange={(_, value) => updateConfig({ task_timeout: value as number })}
                      min={30}
                      max={600}
                      step={30}
                      marks
                      valueLabelDisplay="auto"
                      disabled={updating}
                    />
                  </Box>
                </Box>

                <Box>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={config.enable_load_balancing}
                        onChange={(e) => updateConfig({ enable_load_balancing: e.target.checked })}
                        disabled={updating}
                      />
                    }
                    label="Load Balancing"
                  />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={config.enable_auto_scaling}
                        onChange={(e) => updateConfig({ enable_auto_scaling: e.target.checked })}
                        disabled={updating}
                      />
                    }
                    label="Auto Scaling"
                  />

                  <Box sx={{ mt: 3 }}>
                    <Typography gutterBottom>Scale Up Threshold</Typography>
                    <Slider
                      value={config.scale_up_threshold}
                      onChange={(_, value) => updateConfig({ scale_up_threshold: value as number })}
                      min={0.1}
                      max={1.0}
                      step={0.1}
                      marks
                      valueLabelDisplay="auto"
                      disabled={updating || !config.enable_auto_scaling}
                    />
                  </Box>

                  <Box sx={{ mt: 3 }}>
                    <Typography gutterBottom>Scale Down Threshold</Typography>
                    <Slider
                      value={config.scale_down_threshold}
                      onChange={(_, value) => updateConfig({ scale_down_threshold: value as number })}
                      min={0.1}
                      max={1.0}
                      step={0.1}
                      marks
                      valueLabelDisplay="auto"
                      disabled={updating || !config.enable_auto_scaling}
                    />
                  </Box>
                </Box>
              </Box>
            </Box>
          )}

          {/* Workers Tab */}
          {activeTab === 1 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Worker Status ({workers.length} workers)
              </Typography>

              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Worker ID</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Tasks Completed</TableCell>
                      <TableCell>Tasks Failed</TableCell>
                      <TableCell>CPU Usage</TableCell>
                      <TableCell>Memory Usage</TableCell>
                      <TableCell>Current Task</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {workers.map((worker) => (
                      <TableRow key={worker.id}>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {worker.id}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label={worker.type} size="small" />
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={worker.status} 
                            color={worker.status === 'busy' ? 'warning' : 'success'} 
                            size="small" 
                          />
                        </TableCell>
                        <TableCell>{worker.tasks_completed}</TableCell>
                        <TableCell>{worker.tasks_failed}</TableCell>
                        <TableCell>{worker.cpu_usage.toFixed(1)}%</TableCell>
                        <TableCell>{worker.memory_usage.toFixed(1)}%</TableCell>
                        <TableCell>
                          {worker.current_task ? (
                            <Typography variant="body2" fontFamily="monospace">
                              {worker.current_task}
                            </Typography>
                          ) : '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}

          {/* Tasks Tab */}
          {activeTab === 2 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Recent Tasks ({tasks.length} shown)
              </Typography>

              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Task ID</TableCell>
                      <TableCell>Function</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Priority</TableCell>
                      <TableCell>Processing Time</TableCell>
                      <TableCell>Worker</TableCell>
                      <TableCell>Retries</TableCell>
                      <TableCell>Error</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {tasks.map((task) => (
                      <TableRow key={task.id}>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {task.id.substring(0, 12)}...
                          </Typography>
                        </TableCell>
                        <TableCell>{task.function_name}</TableCell>
                        <TableCell>
                          <Chip 
                            label={task.status} 
                            color={getStatusColor(task.status)} 
                            size="small" 
                          />
                        </TableCell>
                        <TableCell>
                          <Box 
                            sx={{ 
                              width: 8, 
                              height: 8, 
                              borderRadius: '50%', 
                              backgroundColor: getPriorityColor(task.priority),
                              display: 'inline-block',
                              mr: 1
                            }} 
                          />
                          {task.priority}
                        </TableCell>
                        <TableCell>
                          {task.processing_time ? `${task.processing_time.toFixed(2)}s` : '-'}
                        </TableCell>
                        <TableCell>
                          {task.worker_id ? (
                            <Typography variant="body2" fontFamily="monospace">
                              {task.worker_id.substring(0, 12)}...
                            </Typography>
                          ) : '-'}
                        </TableCell>
                        <TableCell>{task.retry_count}</TableCell>
                        <TableCell>
                          {task.error ? (
                            <Tooltip title={task.error}>
                              <Chip label="Error" color="error" size="small" />
                            </Tooltip>
                          ) : '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}

          {/* Metrics Tab */}
          {activeTab === 3 && metrics && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Performance Metrics
              </Typography>

              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 3 }}>
                <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Task Statistics</Typography>
                    <Typography>Submitted: {metrics.tasks_submitted}</Typography>
                    <Typography>Completed: {metrics.tasks_completed}</Typography>
                    <Typography>Failed: {metrics.tasks_failed}</Typography>
                    <Typography>Success Rate: {((metrics.tasks_completed / Math.max(1, metrics.tasks_submitted)) * 100).toFixed(1)}%</Typography>
                  </CardContent>
                </Card>

                <Card sx={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Performance</Typography>
                    <Typography>Avg Processing Time: {metrics.avg_processing_time.toFixed(2)}s</Typography>
                    <Typography>Throughput: {metrics.throughput} tasks/min</Typography>
                    <Typography>Error Rate: {metrics.error_rate.toFixed(1)}%</Typography>
                    <Typography>Queue Size: {metrics.queue_size}</Typography>
                  </CardContent>
                </Card>
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Task Submission Dialog */}
      <Dialog open={showTaskDialog} onClose={() => setShowTaskDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Submit New Task</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Function Name"
              value={taskForm.function_name}
              onChange={(e) => setTaskForm({ ...taskForm, function_name: e.target.value })}
              sx={{ mb: 2 }}
              placeholder="e.g., detect_toxicity"
            />

            <TextField
              fullWidth
              select
              label="Priority"
              value={taskForm.priority}
              onChange={(e) => setTaskForm({ ...taskForm, priority: e.target.value })}
              sx={{ mb: 2 }}
            >
              <MenuItem value="low">Low</MenuItem>
              <MenuItem value="normal">Normal</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="critical">Critical</MenuItem>
            </TextField>

            <TextField
              fullWidth
              type="number"
              label="Timeout (seconds)"
              value={taskForm.timeout}
              onChange={(e) => setTaskForm({ ...taskForm, timeout: parseInt(e.target.value) })}
              sx={{ mb: 2 }}
            />

            <TextField
              fullWidth
              multiline
              rows={3}
              label="Arguments (JSON Array)"
              value={taskForm.args}
              onChange={(e) => setTaskForm({ ...taskForm, args: e.target.value })}
              sx={{ mb: 2 }}
              placeholder='["arg1", "arg2"]'
            />

            <TextField
              fullWidth
              multiline
              rows={3}
              label="Keyword Arguments (JSON Object)"
              value={taskForm.kwargs}
              onChange={(e) => setTaskForm({ ...taskForm, kwargs: e.target.value })}
              placeholder='{"key": "value"}'
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowTaskDialog(false)}>Cancel</Button>
          <Button 
            onClick={submitTask} 
            variant="contained" 
            disabled={submittingTask || !taskForm.function_name}
          >
            {submittingTask ? <CircularProgress size={20} /> : 'Submit Task'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DistributedProcessing;