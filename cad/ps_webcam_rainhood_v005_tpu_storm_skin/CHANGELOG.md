# CHANGELOG

## v0.0.5 — TPU storm skin CAD candidate

- v004 B15 position-retention laneをAuthorityとして新規v005 laneを追加。
- 1.5 mm near-full-contact TPU flat-print skinを追加。
- X/Y 0.5% preloadをparameter化し、0/0.5/1.0% strap couponを追加。
- 9 mm side/rear skirts、1 mm external nose wrap、rear corner drainage reliefを追加。
- 左右前後4点の2.5 mm thick、12 mm head、10 mm root/neck、R2 dogbone/T-headを追加。
- v004 PETG hood外側側壁へ4個の捕捉cageを加算。roof penetrationなし。
- 既存M4案は後方2点とservice-interfering strapのため不採用と記録。
- PETG/TPU anchor couponとTPU acoustic 1.0/1.5/2.0 mm couponsを追加。
- BRep、closed STL edge、STEP re-import、camera/optical/USB/carrier interferenceを自動検証。
- CAD projected-envelopeによる10/20/30 m/s wind load estimateを追加。認証風速は宣言しない。
- v004 source、validation、hood STEPのSHA256をAuthority recordへ固定。
- Statusを`CAD_COMPLETE_TPU_STORM_SKIN_PHYSICAL_VALIDATION_PENDING`に設定。
