#include "receiver.h"

double time_taken = 0.0;
struct timespec start, end;
sem_t *sender_sem = NULL;
sem_t *receiver_sem = NULL;
mailbox_t mailbox;

void receive(message_t *message_ptr, mailbox_t *mailbox_ptr)
{
    /*  TODO:
        1. Use flag to determine the communication method
        2. According to the communication method, receive the message
    */

    if (mailbox_ptr->flag == MSG_PASSING)
    {
        clock_gettime(CLOCK_MONOTONIC, &start);
        int status = msgrcv(mailbox_ptr->storage.msqid, message_ptr, sizeof(message_ptr->msgText), 0, 0);
        clock_gettime(CLOCK_MONOTONIC, &end);
        if (status == -1)
        {
            perror("msgrcv failed");
            exit(1);
        }
    }
    else if (mailbox_ptr->flag == SHARED_MEM)
    {
        clock_gettime(CLOCK_MONOTONIC, &start);
        strcpy(message_ptr->msgText, mailbox_ptr->storage.shm_addr);
        clock_gettime(CLOCK_MONOTONIC, &end);
    }

    if (strcmp(message_ptr->msgText, "exit") != 0)
        printf("\033[36mReceiving message:\033[0m %s", message_ptr->msgText);

    time_taken += ((end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9);
}

int main(int argc, char *argv[])
{
    /*  TODO:
        1) Call receive(&message, &mailbox) according to the flow in slide 4
        2) Measure the total receiving time
        3) Get the mechanism from command line arguments
            • e.g. ./receiver 1
        4) Print information on the console according to the output format
        5) If the exit message is received, print the total receiving time and terminate the receiver.c
    */

    // read command line arguments
    if (argc != 2)
    {
        fprintf(stderr, "Usage: ./receiver <mode>\n");
        fprintf(stderr, "Mode 1 = Message Passing, 2 = Shared Memory\n");
        exit(1);
    }

    mailbox.flag = atoi(argv[1]);
    message_t message;

    if (mailbox.flag == MSG_PASSING)
        printf("\033[36mMessage Passing\033[0m\n");
    else if (mailbox.flag == SHARED_MEM)
        printf("\033[36mShared Memory\033[0m\n");
    else
    {
        fprintf(stderr, "Invalid mode! Use 1 or 2.\n");
        exit(1);
    }

    // create semaphore
    sender_sem = sem_open("/sender_sem", O_CREAT, 0644, 1);
    receiver_sem = sem_open("/receiver_sem", O_CREAT, 0644, 0);
    if (sender_sem == SEM_FAILED || receiver_sem == SEM_FAILED)
    {
        perror("sem_open failed");
        exit(1);
    }

    // create IPC（Message Queue or Shared Memory）
    key_t key = ftok("receiver.c", 'B');
    if (key == -1)
    {
        perror("ftok failed");
        exit(1);
    }

    if (mailbox.flag == MSG_PASSING)
    {
        int id = msgget(key, 0666 | IPC_CREAT);
        if (id == -1)
        {
            perror("msgget failed");
            exit(1);
        }
        mailbox.storage.msqid = id;
    }
    else if (mailbox.flag == SHARED_MEM)
    {
        int shm_id = shmget(key, sizeof(message.msgText), 0666 | IPC_CREAT);
        if (shm_id == -1)
        {
            perror("shmget failed");
            exit(1);
        }

        char *shm_addr = shmat(shm_id, NULL, 0);
        if (shm_addr == (char *)-1)
        {
            perror("shmat failed");
            exit(1);
        }
        mailbox.storage.shm_addr = shm_addr;
    }

    // receive messages
    while (1)
    {
        sem_wait(receiver_sem);
        receive(&message, &mailbox);
        if (strcmp(message.msgText, "exit") == 0)
            break;
        sem_post(sender_sem);
    }

    printf("\n\033[31mSender Exit!\033[0m\n");
    printf("Total time taken in receiving messages: %f seconds\n", time_taken);

    // cleanup
    sem_close(sender_sem);
    sem_close(receiver_sem);
    sem_unlink("/sender_sem");
    sem_unlink("/receiver_sem");

    if (mailbox.flag == SHARED_MEM)
    {
        shmdt(mailbox.storage.shm_addr);
        shmctl(shmget(key, sizeof(message.msgText), 0666 | IPC_CREAT), IPC_RMID, NULL);
    }
    else if (mailbox.flag == MSG_PASSING)
    {
        msgctl(mailbox.storage.msqid, IPC_RMID, NULL);
    }

    return 0;
}
