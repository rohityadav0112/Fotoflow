// console.log('This is Runnig Link')
document.addEventListener("DOMContentLoaded", () => {
    const likeBtn = document.getElementById("like-btn");
    const likeCount = document.getElementById("like-count");
    const commentInput = document.getElementById("comment-input");
    const sendCommentBtn = document.getElementById("send-comment");
    const commentsSection = document.getElementById("comments-section");
    const replyFormTemplate = document.getElementById("reply-form-template");
    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${wsScheme}://${window.location.host}/ws/post/${postId}/`);

    // Like/Unlike
    likeBtn.addEventListener("click", () => {
        const isLiked = likeBtn.dataset.liked === "true";
        socket.send(JSON.stringify({
            type: "toggle_like",
            username: username,
            is_liked: isLiked
        }));
    });

    // Send comment
    sendCommentBtn.addEventListener("click", () => {
        const text = commentInput.value.trim();
        if (text.length > 0) {
            socket.send(JSON.stringify({
                type: "new_comment",
                username: username,
                text: text
            }));
            commentInput.value = "";
        }
    });

    // Send reply (delegated listener)
    commentsSection.addEventListener("click", (e) => {
        if (e.target.classList.contains("reply-btn")) {
            const commentId = e.target.dataset.parentId;
            let commentDiv = e.target.closest(".comment");

            if (!commentDiv.querySelector(".reply-input")) {
                const replyForm = replyFormTemplate.cloneNode(true);
                replyForm.style.display = "block";
                commentDiv.appendChild(replyForm);

                const replyInput = replyForm.querySelector(".reply-input");
                const sendReplyBtn = replyForm.querySelector(".send-reply");

                sendReplyBtn.addEventListener("click", () => {
                    const replyText = replyInput.value.trim();
                    if (replyText.length > 0) {
                        socket.send(JSON.stringify({
                            type: "new_reply",
                            username: username,
                            text: replyText,
                            parent_id: commentId
                        }));
                        replyForm.remove();
                    }
                });
            }
        }
    });

    // Handle incoming WebSocket messages
    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);

        if (data.type === "like_update_broadcast") {
            document.getElementById("like-count").textContent = data.total_likes;
        }
    
        if (data.type === "like_update_personal") {
            const likeBtn = document.getElementById("like-btn");
            likeBtn.dataset.liked = data.is_liked.toString();
            likeBtn.textContent = data.is_liked ? "❤️ Unlike" : "🤍 Like";
        }

        else if (data.type === "new_comment") {
            const comment = data.comment;
            const commentHTML = `
                <div class="comment" data-comment-id="${comment.id}">
                    <p><strong>${comment.username}</strong>: ${comment.text}</p>
                    <button class="reply-btn" data-parent-id="${comment.id}">Reply</button>
                    <div class="replies"></div>
                </div>
            `;
            commentsSection.insertAdjacentHTML("beforeend", commentHTML);
        }

        else if (data.type === "new_reply") {
            const reply = data.reply;
            const parentDiv = commentsSection.querySelector(`[data-comment-id="${reply.parent_id}"] .replies`);
            const replyHTML = `
                <div class="reply" data-reply-id="${reply.id}">
                    <p><strong>${reply.username}</strong>: ${reply.text}</p>
                </div>
            `;
            parentDiv.insertAdjacentHTML("beforeend", replyHTML);
        }
    };

    socket.onclose = function() {
        console.error("WebSocket closed unexpectedly");
    };
});