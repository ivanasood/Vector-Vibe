# VectorVibe Mathematical Verification

**Verification date:** 2026-10-07  
**Source:** uploaded `Mathminiprojectsongsdataset.xlsx`  
**Method:** recomputed the formulas independently with Python’s built-in arithmetic, `sqrt`, and `acos`, then compared those results with the Flask recommendation API and the browser-rendered playlist. No dataset values or recommendation formulas were changed.

## Dataset and matrix

- Workbook rows: **100 songs**
- Feature columns: **7** — Classical, Pop, Energetic, Peaceful, Romantic, Tempo, Mood
- Matrix shape: **100 × 7** (one song per row, features in the order above)
- Workbook SHA-256: `c11ce7e1c9635d9b0fec6b7831666beaf6e65462ce876e0ff32a3cff2fbbd2ff`
- The bundled workbook hash matched the uploaded workbook hash.

## Independent calculation method

For each real song vector `S` and preference vector `U`, the verification independently calculated:

```text
S · U       = Σ(Sᵢ × Uᵢ)
||S||       = √Σ(Sᵢ²)
||U||       = √Σ(Uᵢ²)
cos(θ)      = (S · U) / (||S|| × ||U||)
θ           = arccos(cos(θ)) × 180/π
proj_U(S)   = ((S · U) / (U · U)) U
```

The shared user vector for the three-song check was:

```text
U = [0.27, 0.73, 0.46, 0.21, 0.68, 0.59, 0.84]
```

### Three real-song comparisons

All three songs below came from the workbook and were returned by the actual Top 10 engine. API values matched the independent calculations; the maximum absolute difference across dot product, norms, cosine, angle, and projection components was **0.0** for each checked song in the calculation run.

| Song | `S` in feature order | `S · U` | `||S||` | `||U||` | Cosine similarity | Angle |
|---|---|---:|---:|---:|---:|---:|
| Vachindamma | `[0.10, 0.75, 0.68, 0.35, 0.90, 0.63, 0.94]` | 2.7341 | 1.802193108410 | 1.541946821392 | 0.983883492848 (98.3883%) | 10.300495099° |
| Sapphire | `[0.02, 0.90, 0.68, 0.38, 0.76, 0.64, 0.86]` | 2.6718 | 1.773132820744 | 1.541946821392 | 0.977222101698 (97.7222%) | 12.252431380° |
| Udi Udi | `[0.04, 0.82, 0.78, 0.22, 0.72, 0.67, 0.91]` | 2.6637 | 1.768106331644 | 1.541946821392 | 0.977029181622 (97.7029%) | 12.304408166° |

Projection vectors, in the same seven-feature order:

```text
Vachindamma: [0.310484102, 0.839457015, 0.528972914, 0.241487635, 0.781959960, 0.678465259, 0.965950538]
Sapphire:    [0.303409320, 0.820328903, 0.516919582, 0.235985027, 0.764141992, 0.663005552, 0.943940108]
Udi Udi:     [0.302489485, 0.817841941, 0.515352456, 0.235269600, 0.761825370, 0.660995542, 0.941078398]
```

For example, the first dot product expands to:

```text
0.10×0.27 + 0.75×0.73 + 0.68×0.46 + 0.35×0.21
+ 0.90×0.68 + 0.63×0.59 + 0.94×0.84 = 2.7341
```

## Identical-vector check

Using the actual workbook vector for **Aaoge Tum Kabhi** as both `S` and `U`:

- Cosine similarity: **0.9999999999999998**, i.e. approximately **1**
- Angle: **0.000001207°**, effectively **0°**
- Projection: matches the song vector

The tiny nonzero angle is floating-point round-off from evaluating `arccos` on a cosine just below 1; it is within the existing `1e-5°` zero-angle tolerance and is not a formula discrepancy.

## Zero-vector check

For `U = [0, 0, 0, 0, 0, 0, 0]`:

- The API processed all 100 songs without division by zero.
- Cosine similarity is safely defined as **0** for every song; the Top 10 therefore retain workbook order for the tie.
- The angle is undefined (`null` in the API) because a zero vector has no direction.
- The projection result is a seven-value zero vector, safely returned rather than dividing by `U · U = 0`.
- The results panel immediately explains that the zero preference vector has no direction, all cosine scores are 0, and angle/projection are mathematically undefined. After selecting a song, the detailed analysis displays **“Undefined (a zero vector has no direction)”** for the angle and explains the safe zero-vector projection result.

## Ranking and displayed Top 10

For the shared `U` above, the independent verifier computed cosine similarity for **all 100 workbook rows**, sorted by descending score with workbook order as the tie-break, and compared that list with the API’s all-100 similarity distribution. The maximum absolute score difference was **0.0**. The API Top 10 IDs equalled both the first ten API distribution IDs and the first ten independently ranked workbook IDs.

The browser-rendered Top 10 was also compared against those same API results; it displayed exactly these ten songs in the same order:

| Rank | Song | Cosine similarity |
|---:|---|---:|
| 1 | Vachindamma | 98.3883% |
| 2 | Sapphire | 97.7222% |
| 3 | Udi Udi | 97.7029% |
| 4 | Cheri Cheri Lady | 97.4002% |
| 5 | The Fate of Ophelia | 97.3937% |
| 6 | Uff | 97.2926% |
| 7 | Ride It | 97.2484% |
| 8 | Odiyamma | 97.2345% |
| 9 | Pretty Little Baby | 97.1638% |
| 10 | Na Ja | 97.1297% |

## Result

**The calculations are correct** within floating-point precision. The independent calculations, API values, complete 100-song similarity order, and browser-rendered Top 10 agreed. The zero-vector case is guarded and communicated in the selected-song analysis. No underlying implementation change was needed.

Regression tests for the independent formulas and ranking are in `tests/test_math_verification.py`.
