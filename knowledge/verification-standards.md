# Verification Standards & Thresholds

- **Aadhaar Checksum**: 12-digit numeric string, cannot begin with `0` or `1`, must satisfy the Verhoeff dihedral group $D_5$ checksum (`c == 0`), and must be masked to `XXXX-XXXX-<last4>`.
- **Driving License Format**: 2-letter authorized Indian RTO state code followed by 2-digit RTO code, 4-digit issue year (`1960`–`2027`), and 7-digit unique identifier.
- **Image Quality**: Laplacian variance $\ge 65.0$ required for sharp document edge clarity.
- **Facial Biometrics**: 256-dimensional L2-normalized embedding cosine similarity $\ge 0.75$ for `MATCH`.
- **Physiological Liveness**: MAX30102 infrared PPG pulsatile waveform with `signal_quality >= 0.65` and heart rate between $45$ and $165\text{ BPM}$.
