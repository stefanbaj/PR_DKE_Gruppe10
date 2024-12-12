import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-chatbot',
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.scss'],
})
export class ChatbotComponent {
  userMessage: string = ''; // Input message from the user
  chatHistory: { timestamp: string; messages: { sender: string; text: string }[] }[] = []; // List of chat sessions
  currentChat: { sender: string; text: string }[] = []; // Messages in the active chat session
  currentChatIndex: number | null = null; // Index of the currently active chat session

  constructor(private http: HttpClient) {}

  // Starts a new chat session
  startNewChat(): void {
    // Save the current chat session if it exists
    if (this.currentChat.length > 0) {
      const timestamp = new Date().toLocaleString();
      if (this.currentChatIndex !== null) {
        this.chatHistory[this.currentChatIndex] = {
          timestamp,
          messages: [...this.currentChat],
        };
      } else {
        this.chatHistory.push({ timestamp, messages: [...this.currentChat] });
      }
    }

    // Initialize a new chat session
    const newTimestamp = new Date().toLocaleString();
    this.currentChat = [];
    this.currentChatIndex = this.chatHistory.length;
    this.chatHistory.push({ timestamp: newTimestamp, messages: this.currentChat });
  }

  // Loads a selected chat session from the sidebar
  loadChat(index: number): void {
    // Save the current chat session
    if (this.currentChatIndex !== null && this.currentChat.length > 0) {
      const timestamp = new Date().toLocaleString();
      this.chatHistory[this.currentChatIndex] = {
        timestamp,
        messages: [...this.currentChat],
      };
    }

    // Load the selected chat session
    this.currentChatIndex = index;
    this.currentChat = [...this.chatHistory[index].messages];
  }

  // Sends a message in the current chat session
  sendMessage(): void {
    if (!this.userMessage.trim()) return;

    // Add the user's message to the current chat
    const userMessage = { sender: 'user', text: this.userMessage };
    this.currentChat.push(userMessage);

    // Add the user's message to the UI
    this.userMessage = ''; // Clear the input field

    // Send the message to the backend
    this.http
      .post<any>('http://localhost:8000/ask', { query: userMessage.text })
      .subscribe({
        next: (response) => {
          // Access the "result" field from the response
          const botMessage = { sender: 'bot', text: response.response.result };
          this.currentChat.push(botMessage); // Add bot's response to the current chat
        },
        error: (error) => {
          const errorMessage = { sender: 'bot', text: 'Error: ' + error.message };
          this.currentChat.push(errorMessage); // Add error message to the current chat
        },
      });
  }
}
