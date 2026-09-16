#include "sender.h"

double time_taken = 0.0;
struct timespec start, end;
sem_t *sender_sem = NULL;
sem_t *receiver_sem = NULL;
mailbox_t mailbox;

void send(message_t message, mailbox_t *mailbox_ptr)
{
    /*  TODO:
        1. Use flag to determine the communication method
        2. According to the communication method, send the message
    */
    // Message Passing
    if (mailbox_ptr->flag == MSG_PASSING)
    {
        clock_gettime(CLOCK_MONOTONIC, &start);
        int status = msgsnd(mailbox_ptr->storage.msqid, &message, sizeof(message.msgText), 0);
        clock_gettime(CLOCK_MONOTONIC, &end);
        if (status == -1)
        {
            perror("msgsnd failed");
            exit(1);
        }
    }

    // Shared Memory
    else if (mailbox_ptr->flag == SHARED_MEM)
    {
        clock_gettime(CLOCK_MONOTONIC, &start);
        strcpy(mailbox_ptr->storage.shm_addr, message.msgText);
        clock_gettime(CLOCK_MONOTONIC, &end);
    }

    if (strcmp(message.msgText, "exit") != 0)
        printf("\033[36mSending message:\033[0m %s", message.msgText);

    time_taken += ((end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9);
}

int main(int argc, char *argv[])
{
    /*  TODO:
        1) Call send(message, &mailbox) according to the flow in slide 4
        2) Measure the total sending time
        3) Get the mechanism and the input file from command line arguments
            • e.g. ./sender 1 input.txt
                    (1 for Message Passing, 2 for Shared Memory)
        4) Get the messages to be sent from the input file
        5) Print information on the console according to the output format
        6) If the message form the input file is EOF, send an exit message to the receiver.c
        7) Print the total sending time and terminate the sender.c
    */

    // read command line arguments
    if (argc != 3)
    {
        fprintf(stderr, "Usage: ./sender <mode> <input_file>\n");
        fprintf(stderr, "Mode 1 = Message Passing, 2 = Shared Memory\n");
        exit(1);
    }

    mailbox.flag = atoi(argv[1]);
    char *file_name = argv[2];
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

    // open input file
    FILE *file = fopen(file_name, "r");
    if (!file)
    {
        perror("Error opening input file");
        exit(1);
    }

    // send messages
    while (fgets(message.msgText, sizeof(message.msgText), file))
    {
        sem_wait(sender_sem);
        message.mType = 1;
        send(message, &mailbox);
        sem_post(receiver_sem);
    }

    // send exit message
    sem_wait(sender_sem);
    strcpy(message.msgText, "exit");
    message.mType = 1;
    send(message, &mailbox);
    sem_post(receiver_sem);

    printf("\n\033[31mEnd of input file! exit!\033[0m\n");
    printf("Total time taken in sending messages: %f seconds\n", time_taken);

    // cleanup
    fclose(file);
    sem_close(sender_sem);
    sem_close(receiver_sem);
    sem_unlink("/sender_sem");
    sem_unlink("/receiver_sem");

    if (mailbox.flag == SHARED_MEM)
        shmdt(mailbox.storage.shm_addr);

    return 0;
}
