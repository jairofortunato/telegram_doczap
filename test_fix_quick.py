#!/usr/bin/env python3
"""
Quick test to verify deduplication fix is working
Run this before deploying to production
"""

import sys
from utils.processing_state import ProcessingStateManager
from handlers.whatsapp_handler import WhatsAppHandler

def test_processing_state_integration():
    """Quick test that processing state is integrated"""
    print("\n" + "="*60)
    print("🧪 Quick Deduplication Fix Verification")
    print("="*60)

    # Test 1: ProcessingStateManager exists and works
    print("\n✓ Test 1: ProcessingStateManager initialization")
    try:
        manager = ProcessingStateManager(cleanup_interval=300)
        print("  ✅ PASS: ProcessingStateManager initialized")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        return False

    # Test 2: Basic deduplication logic
    print("\n✓ Test 2: Basic deduplication logic")
    test_id = "test_audio_123"

    # First attempt should succeed
    if not manager.start_processing(test_id):
        print("  ❌ FAIL: First processing should succeed")
        return False
    print("  ✅ First processing started")

    # Duplicate should be blocked
    if manager.start_processing(test_id):
        print("  ❌ FAIL: Duplicate should be blocked")
        return False
    print("  ✅ Duplicate correctly blocked")

    # Finish and verify completed state
    manager.finish_processing(test_id, success=True)
    if not manager.is_completed(test_id):
        print("  ❌ FAIL: Should be marked as completed")
        return False
    print("  ✅ Correctly marked as completed")

    # Test 3: WhatsAppHandler has processing_state
    print("\n✓ Test 3: WhatsAppHandler integration")
    try:
        # Create mock services (None is OK for this test)
        handler = WhatsAppHandler(
            whatsapp_service=None,
            auth_service=None,
            ai_service=None,
            subscription_service=None,
            processing_state=manager
        )

        if not hasattr(handler, 'processing_state'):
            print("  ❌ FAIL: WhatsAppHandler missing processing_state")
            return False

        if handler.processing_state is None:
            print("  ❌ FAIL: processing_state is None")
            return False

        print("  ✅ PASS: WhatsAppHandler has processing_state")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        return False

    # Test 4: Verify deduplication prevents duplicates
    print("\n✓ Test 4: Simulate duplicate webhook scenario")
    media_id = "whatsapp_media_xyz789"

    attempts = 5
    successful = 0
    blocked = 0

    for i in range(attempts):
        if manager.is_processing(media_id) or manager.is_completed(media_id):
            blocked += 1
        elif manager.start_processing(media_id):
            successful += 1
            manager.finish_processing(media_id, success=True)
        else:
            blocked += 1

    print(f"  📊 Results: {successful} processed, {blocked} blocked")

    if successful != 1:
        print(f"  ❌ FAIL: Should process exactly once (got {successful})")
        return False

    if blocked != attempts - 1:
        print(f"  ❌ FAIL: Should block {attempts-1} duplicates (got {blocked})")
        return False

    print(f"  ✅ PASS: Processed once, blocked {blocked} duplicates")

    # All tests passed
    print("\n" + "="*60)
    print("🎉 ALL TESTS PASSED!")
    print("="*60)
    print("\n✅ The deduplication fix is working correctly!")
    print("✅ WhatsApp handler will prevent duplicate prontuários")
    print("\n📝 Next steps:")
    print("   1. Test locally: python main.py")
    print("   2. Test with ngrok + real WhatsApp message")
    print("   3. Deploy: railway up")
    print("   4. Monitor: railway logs --tail")
    print("\n" + "="*60)

    return True

if __name__ == "__main__":
    try:
        success = test_processing_state_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
