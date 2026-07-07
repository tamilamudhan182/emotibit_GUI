#!/usr/bin/env python
"""
QUICK START EXAMPLES - Morphology Analysis
============================================
Copy-paste ready examples for common tasks.
Run directly: python quick_start.py
"""

from morphology_analyzer import MorphologyAnalyzer
import pandas as pd

# ============================================================================
# EXAMPLE 1: Analyze a single file (output to same directory)
# ============================================================================
print("=" * 70)
print("EXAMPLE 1: Single File Analysis")
print("=" * 70)

analyzer = MorphologyAnalyzer('emotibit_record.csv')
analyzer.analyze()


# ============================================================================
# EXAMPLE 2: Analyze and save to specific output folder
# ============================================================================
print("\n" + "=" * 70)
print("EXAMPLE 2: Analysis with Custom Output Directory")
print("=" * 70)

# analyzer = MorphologyAnalyzer('emotibit_record.csv', output_dir='./results')
# analyzer.analyze()
# print("Results saved to ./results")


# ============================================================================
# EXAMPLE 3: Get just the metrics (no plots)
# ============================================================================
print("\n" + "=" * 70)
print("EXAMPLE 3: Extract Metrics Programmatically")
print("=" * 70)

analyzer = MorphologyAnalyzer('emotibit_record.csv')

print("\nMetrics for each signal:")
print("-" * 70)

for signal_name in sorted(analyzer.signals.keys()):
    signal = analyzer.signals[signal_name]
    metrics = analyzer.compute_morphology(signal, signal_name)
    
    print(f"\n{signal_name}:")
    print(f"  Mean: {metrics['mean']:.4f}")
    print(f"  Std:  {metrics['std']:.4f}")
    print(f"  Peaks: {metrics['peaks_count']}")
    print(f"  Range: {metrics['min']:.4f} to {metrics['max']:.4f}")


# ============================================================================
# EXAMPLE 4: Save metrics to DataFrame for analysis
# ============================================================================
print("\n" + "=" * 70)
print("EXAMPLE 4: Metrics as DataFrame")
print("=" * 70)

analyzer = MorphologyAnalyzer('emotibit_record.csv')
metrics_list = []

for signal_name in sorted(analyzer.signals.keys()):
    signal = analyzer.signals[signal_name]
    metrics = analyzer.compute_morphology(signal, signal_name)
    
    metrics_list.append({
        'Signal': signal_name,
        'Mean': metrics['mean'],
        'Std': metrics['std'],
        'Min': metrics['min'],
        'Max': metrics['max'],
        'Peaks': metrics['peaks_count'],
        'Range': metrics['range'],
    })

df = pd.DataFrame(metrics_list)
print("\n", df.to_string(index=False))


# ============================================================================
# EXAMPLE 5: Find all peaks and their times
# ============================================================================
print("\n" + "=" * 70)
print("EXAMPLE 5: Peak Detection Details")
print("=" * 70)

analyzer = MorphologyAnalyzer('emotibit_record.csv')

for signal_name in ['EDA', 'PPG-IR', 'PPG-Red', 'PPG-Green']:
    if signal_name in analyzer.signals:
        signal = analyzer.signals[signal_name]
        metrics = analyzer.compute_morphology(signal, signal_name)
        
        peak_idx = metrics['peaks_idx']
        peak_times = analyzer.time[peak_idx]
        peak_values = signal[peak_idx]
        
        print(f"\n{signal_name} - {len(peak_idx)} peaks found:")
        print(f"  Times: {peak_times[:5]}...") if len(peak_times) > 5 else print(f"  Times: {peak_times}")
        print(f"  Values: {peak_values[:5]}...") if len(peak_values) > 5 else print(f"  Values: {peak_values}")


# ============================================================================
# EXAMPLE 6: Compare statistics across signals
# ============================================================================
print("\n" + "=" * 70)
print("EXAMPLE 6: Signal Comparison")
print("=" * 70)

analyzer = MorphologyAnalyzer('emotibit_record.csv')

comparison = {
    'Signal': [],
    'Mean': [],
    'Std': [],
    'CV (%)': [],  # Coefficient of variation
    'Peaks': [],
}

for signal_name in sorted(analyzer.signals.keys()):
    signal = analyzer.signals[signal_name]
    metrics = analyzer.compute_morphology(signal, signal_name)
    
    cv = (metrics['std'] / abs(metrics['mean']) * 100) if metrics['mean'] != 0 else 0
    
    comparison['Signal'].append(signal_name)
    comparison['Mean'].append(metrics['mean'])
    comparison['Std'].append(metrics['std'])
    comparison['CV (%)'].append(cv)
    comparison['Peaks'].append(metrics['peaks_count'])

df_compare = pd.DataFrame(comparison)
print("\n", df_compare.to_string(index=False))
print(f"\nHighest variability (CV): {df_compare.loc[df_compare['CV (%)'].idxmax(), 'Signal']}")


# ============================================================================
# EXAMPLE 7: Batch analysis (template for multiple files)
# ============================================================================
print("\n" + "=" * 70)
print("EXAMPLE 7: Batch Processing Template")
print("=" * 70)

"""
Uncomment and modify this to analyze multiple files:

from pathlib import Path

data_files = [
    'data1.csv',
    'data2.csv',
    'data3.csv',
]

results = []

for file in data_files:
    try:
        analyzer = MorphologyAnalyzer(file)
        
        for signal_name in sorted(analyzer.signals.keys()):
            signal = analyzer.signals[signal_name]
            metrics = analyzer.compute_morphology(signal, signal_name)
            
            results.append({
                'File': file,
                'Signal': signal_name,
                'Mean': metrics['mean'],
                'Std': metrics['std'],
                'Peaks': metrics['peaks_count'],
            })
    except Exception as e:
        print(f"Error processing {file}: {e}")

df_batch = pd.DataFrame(results)
df_batch.to_csv('batch_results.csv', index=False)
print("Batch analysis complete! Results saved to batch_results.csv")
"""

print("Batch processing example shown in comments. Uncomment to use.")


# ============================================================================
# EXAMPLE 8: Custom analysis - find outlier peaks
# ============================================================================
print("\n" + "=" * 70)
print("EXAMPLE 8: Find Outlier Peaks")
print("=" * 70)

analyzer = MorphologyAnalyzer('emotibit_record.csv')

if 'EDA' in analyzer.signals:
    signal = analyzer.signals['EDA']
    metrics = analyzer.compute_morphology(signal, 'EDA')
    
    peak_values = signal[metrics['peaks_idx']]
    mean_peak = peak_values.mean()
    std_peak = peak_values.std()
    
    # Find peaks > 2 std deviations from mean
    outliers = peak_values > (mean_peak + 2*std_peak)
    
    print(f"\nEDA Peak Statistics:")
    print(f"  Total peaks: {len(peak_values)}")
    print(f"  Mean peak value: {mean_peak:.6f}")
    print(f"  Std of peaks: {std_peak:.6f}")
    print(f"  Outlier peaks (>2 std): {outliers.sum()}")
    
    if outliers.sum() > 0:
        outlier_values = peak_values[outliers]
        print(f"  Outlier values: {outlier_values}")


print("\n" + "=" * 70)
print("Examples complete! Check output files:")
print("  - morphology_signals.png")
print("  - morphology_metrics.png")
print("  - morphology_metrics.csv")
print("=" * 70)
