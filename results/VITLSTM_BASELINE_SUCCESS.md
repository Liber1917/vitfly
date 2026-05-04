# ViTLSTM Baseline Test Results - SUCCESS

**Date**: 2026-05-04  
**Branch**: main (upstream vitfly repository)  
**Model**: ViTLSTM_model.pth (14MB)  
**Test Command**: `bash launch_evaluation.bash 1 vision`

## Test Status: ✅ SUCCESS

The original ViTLSTM baseline from the ICRA 2025 paper ran successfully on the main branch.

## Results Summary

```yaml
rollout_1:
  Success: true
  number_crashes: 0
  segment_times:
    '10': 2.19s
    '20': 4.30s
    '30': 6.25s
    '40': 8.25s
    '50': 10.25s
    '60': 12.28s
  time_to_finish: 12.28s
```

### Performance Metrics

- **Course Length**: 60 meters
- **Completion Time**: 12.28 seconds
- **Average Speed**: 4.89 m/s
- **Crashes**: 0
- **Success Rate**: 100% (1/1 trials)

## Model Details

- **Architecture**: Vision Transformer + LSTM
- **Input**: Depth images (from camera)
- **Output**: Velocity commands (vx, vy, vz)
- **Model File**: `/root/catkin_ws/src/vitfly-mambatest/models/ViTLSTM_model.pth`
- **Model Size**: 14MB

## Test Environment

- **Simulator**: Flightmare (Unity-based)
- **ROS**: Noetic
- **Python**: 3.13.12
- **PyTorch**: 2.11.0+cu130
- **NumPy**: 1.26.4 (downgraded from 2.x for ROS compatibility)

## Dependency Issues Resolved

The test initially failed due to missing Python dependencies. The following packages were installed:

1. **pyyaml** - YAML parsing
2. **rospkg** - ROS package management
3. **numpy<2** - Downgraded for ROS cv_bridge compatibility
4. **scipy** - Scientific computing
5. **uniplot** - Terminal plotting
6. **pandas** - Data analysis
7. **opencv-python<4.10** - Computer vision (older version for numpy 1.x compatibility)
8. **torch** - PyTorch deep learning framework

### Critical Compatibility Issue

- **opencv-python 4.13+** requires numpy>=2
- **ROS cv_bridge** requires numpy<2
- **Solution**: Installed opencv-python 4.9.0.80 which works with numpy 1.26.4

## Model Loading

The model loaded successfully without dimension mismatch errors. This confirms:

1. The upstream ViTLSTM model is correctly configured
2. No input dimension issues (unlike the mambatest-distill branch issue)
3. The model architecture matches the checkpoint

## Flight Execution

- **Takeoff**: Successful (minimum snap trajectory)
- **Obstacle Avoidance**: Successful (0 crashes)
- **Velocity Commands**: Sent via ROS topic `/kingfisher/dodgeros_pilot/velocity_command`
- **Course Completion**: Full 60m course completed

## Comparison to mambatest-distill Issue

On the mambatest-distill branch, ViTLSTM had an input dimension mismatch:
- **Expected**: 517 features
- **Actual**: 519 features
- **Error**: RuntimeError during model loading

On the main branch (this test):
- **No dimension mismatch**
- **Model loads successfully**
- **Test completes successfully**

This confirms the dimension mismatch was introduced in the mambatest-distill branch modifications, not in the original upstream code.

## Segment Time Analysis

| Segment | Time (s) | Segment Speed (m/s) |
|---------|----------|---------------------|
| 0-10m   | 2.19     | 4.57                |
| 10-20m  | 2.11     | 4.74                |
| 20-30m  | 1.95     | 5.13                |
| 30-40m  | 2.00     | 5.00                |
| 40-50m  | 2.00     | 5.00                |
| 50-60m  | 2.03     | 4.93                |

The drone maintains relatively consistent speed throughout the course, with slight acceleration in the middle segments.

## Conclusion

The original ViTLSTM baseline from the ICRA 2025 paper works correctly on the main branch:

✅ Model loads without errors  
✅ Simulator connects successfully  
✅ Drone completes full 60m course  
✅ Zero crashes  
✅ Average speed: 4.89 m/s  

This establishes a working baseline for comparison with the Mamba experimental branches.

## Next Steps

1. Compare this baseline performance with Mamba branch results
2. Investigate the dimension mismatch on mambatest-distill branch
3. Run multiple trials for statistical significance
4. Test on different obstacle configurations

## Files Generated

- `/root/catkin_ws/src/vitfly-mambatest/evaluation.yaml` - Test results
- `/root/catkin_ws/src/vitfly-mambatest/envtest/ros/summary.yaml` - Summary metrics
- `/tmp/vitlstm_success_run.log` - Full test log
