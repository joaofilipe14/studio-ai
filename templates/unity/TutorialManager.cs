using UnityEngine;
using UnityEngine.UIElements;

public static class TutorialManager {

    public static void ShowTutorial() {
        UIDocument uiDoc = Object.FindAnyObjectByType<UIDocument>();
        if (uiDoc == null) return;

        VisualTreeAsset tutorialAsset = Resources.Load<VisualTreeAsset>("UI/Tutorial");
        if (tutorialAsset == null) {
            Debug.LogError("Não encontrei o Tutorial.uxml na pasta Resources!");
            return;
        }

        VisualElement tutorialRoot = tutorialAsset.Instantiate();
        tutorialRoot.style.position = Position.Absolute;
        tutorialRoot.style.left = 0;
        tutorialRoot.style.right = 0;
        tutorialRoot.style.top = 0;
        tutorialRoot.style.bottom = 0;

        // Adiciona apenas UMA vez!
        uiDoc.rootVisualElement.Add(tutorialRoot);
        tutorialRoot.BringToFront();

        // Pausa o jogo e mostra o cursor
        Time.timeScale = 0f;

        tutorialRoot.schedule.Execute(() => {
            UnityEngine.Cursor.visible = true;
            UnityEngine.Cursor.lockState = CursorLockMode.None;
        }).Every(50);
        EventCallback<KeyDownEvent> onKeyDown = null;

        void CloseTutorial() {
            if (uiDoc.rootVisualElement.Contains(tutorialRoot)) {
                uiDoc.rootVisualElement.Remove(tutorialRoot);
            }
            if (onKeyDown != null) {
                uiDoc.rootVisualElement.UnregisterCallback(onKeyDown, TrickleDown.TrickleDown);
            }
            UIManager.Instance.ShowHUD();
            UnityEngine.Cursor.visible = false;
            UnityEngine.Cursor.lockState = CursorLockMode.Locked;
            Time.timeScale = 1f;
        }
        Button closeBtn = tutorialRoot.Q<Button>("btn-close");
        if (closeBtn != null) {
            closeBtn.clicked += CloseTutorial;
        }
        onKeyDown = (evt) => {
            if (evt.keyCode == KeyCode.Escape) {
                CloseTutorial();
            }
        };
        uiDoc.rootVisualElement.RegisterCallback(onKeyDown, TrickleDown.TrickleDown);
    }
}