import 'dart:async';

import 'package:in_app_purchase/in_app_purchase.dart';

import '../store.dart';

/// Google Play Billing wrapper. Product IDs must match the subscriptions
/// created in Play Console > Monetize > Subscriptions.
class Subscription {
  static const monthlyId = 'sura_premium_monthly';
  static const yearlyId = 'sura_premium_yearly';

  final AppState state;
  final _iap = InAppPurchase.instance;
  StreamSubscription<List<PurchaseDetails>>? _sub;
  List<ProductDetails> products = [];

  Subscription(this.state);

  Future<void> init() async {
    if (!await _iap.isAvailable()) return;
    _sub = _iap.purchaseStream.listen(_onPurchases);
    final r = await _iap.queryProductDetails({monthlyId, yearlyId});
    products = r.productDetails;
    await _iap.restorePurchases();
  }

  Future<void> _onPurchases(List<PurchaseDetails> list) async {
    for (final p in list) {
      if (p.status == PurchaseStatus.purchased ||
          p.status == PurchaseStatus.restored) {
        // TODO(production): verify p.verificationData on your server.
        await state.setPremium(true);
      }
      if (p.pendingCompletePurchase) await _iap.completePurchase(p);
    }
  }

  Future<void> buy(ProductDetails p) =>
      _iap.buyNonConsumable(purchaseParam: PurchaseParam(productDetails: p));

  Future<void> restore() => _iap.restorePurchases();

  void dispose() => _sub?.cancel();
}
